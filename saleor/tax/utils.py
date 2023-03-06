from decimal import Decimal
from typing import TYPE_CHECKING, Iterable, Optional, Tuple

from prices import TaxedMoney

if TYPE_CHECKING:
    from ..account.models import Address
    from ..channel.models import Channel
    from ..checkout.fetch import CheckoutInfo, CheckoutLineInfo
    from ..order.models import Order
    from ..tax.models import TaxClass, TaxClassCountryRate
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


def get_tax_calculation_strategy_for_order(order: "Order"):
    """Get tax_calculation_strategy value for order."""
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
    return get_tax_calculation_strategy(tax_configuration, country_tax_configuration)


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
    """Get tax_calculation_strategy value for checkout."""
    tax_configuration, country_tax_configuration = _get_tax_configuration_for_checkout(
        checkout_info, lines
    )
    return get_tax_calculation_strategy(tax_configuration, country_tax_configuration)


def normalize_tax_rate_for_db(tax_rate: Decimal) -> Decimal:
    # Percentage values are used to represent tax rates in tax apps and flat rates, but
    # in the database rates are stored as fractional values. Example: tax app returns
    # `10%` as `10`, but in the database it's stored as `0.1`.
    return tax_rate / 100


def denormalize_tax_rate_from_db(tax_rate: Decimal) -> Decimal:
    # Revert results of `normalize_tax_rate_for_db`.
    return tax_rate * 100


def calculate_tax_rate(price: TaxedMoney) -> Decimal:
    """Calculate the tax rate as percentage value from given price.

    Requires a TaxedMoney instance with net and gross amounts set.
    """
    tax_rate = Decimal("0.0")
    # The condition will return False when unit_price.gross or unit_price.net is 0.0
    if not isinstance(price, Decimal) and all((price.gross, price.net)):
        tax_rate = price.tax / price.net
    return tax_rate


def get_tax_rate_for_tax_class(
    tax_class: Optional["TaxClass"],
    tax_class_country_rates: Iterable["TaxClassCountryRate"],
    default_tax_rate: Decimal,
    country_code: str,
) -> Decimal:
    tax_rate = default_tax_rate
    if tax_class:
        for country_rate in tax_class_country_rates:
            if country_rate.country == country_code:
                tax_rate = country_rate.rate
    return tax_rate


def get_tax_class_kwargs_for_order_line(tax_class: Optional["TaxClass"]):
    if not tax_class:
        return {}

    return {
        "tax_class": tax_class,
        "tax_class_name": tax_class.name,
        "tax_class_private_metadata": tax_class.private_metadata,
        "tax_class_metadata": tax_class.metadata,
    }


def get_shipping_tax_class_kwargs_for_order(tax_class: Optional["TaxClass"]):
    if not tax_class:
        return {}

    return {
        "shipping_tax_class": tax_class,
        "shipping_tax_class_name": tax_class.name,
        "shipping_tax_class_private_metadata": tax_class.private_metadata,
        "shipping_tax_class_metadata": tax_class.metadata,
    }
