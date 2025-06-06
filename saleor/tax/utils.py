import logging
from collections import defaultdict
from collections.abc import Iterable
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from django.conf import settings
from prices import TaxedMoney

from ..core.utils.country import get_active_country
from ..tax.models import TaxClass, TaxClassCountryRate
from . import TaxCalculationStrategy

if TYPE_CHECKING:
    from ..checkout.fetch import CheckoutInfo, CheckoutLineInfo
    from ..checkout.models import CheckoutLine
    from ..order.models import Order, OrderLine
    from .models import TaxConfiguration, TaxConfigurationPerCountry


logger = logging.getLogger(__name__)


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
) -> str:
    """Get tax_calculation_strategy value for tax channel configuration.

    :param channel_tax_configuration: Channel-specific tax configuration.
    :param country_tax_configuration: Country-specific tax configuration for the given
    channel.
    """
    return (
        country_tax_configuration.tax_calculation_strategy
        if country_tax_configuration
        else channel_tax_configuration.tax_calculation_strategy
    ) or TaxCalculationStrategy.FLAT_RATES


def should_use_weighted_tax_for_shipping(
    channel_tax_configuration: "TaxConfiguration",
    country_tax_configuration: Optional["TaxConfigurationPerCountry"],
) -> bool:
    """Get use_weighted_tax_for_shipping value for tax channel configuration."""
    tax_calculation_strategy = get_tax_calculation_strategy(
        channel_tax_configuration, country_tax_configuration
    )
    if tax_calculation_strategy != TaxCalculationStrategy.FLAT_RATES:
        return False
    return (
        country_tax_configuration.use_weighted_tax_for_shipping
        if country_tax_configuration
        else channel_tax_configuration.use_weighted_tax_for_shipping
    )


def get_tax_app_id(
    channel_tax_configuration: "TaxConfiguration",
    country_tax_configuration: Optional["TaxConfigurationPerCountry"],
) -> str | None:
    """Get tax_app_id value for tax channel configuration.

    :param channel_tax_configuration: Channel-specific tax configuration.
    :param country_tax_configuration: Country-specific tax configuration for the given
    channel.
    """
    return (
        country_tax_configuration.tax_app_id
        if country_tax_configuration and country_tax_configuration.tax_app_id
        else channel_tax_configuration.tax_app_id
    )


def _get_tax_configuration_for_order(
    order: "Order",
) -> tuple["TaxConfiguration", Optional["TaxConfigurationPerCountry"]]:
    channel = order.channel
    tax_configuration = channel.tax_configuration
    country_code = get_active_country(
        channel,
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
    return tax_configuration, country_tax_configuration


def get_charge_taxes_for_order(order: "Order") -> bool:
    """Get charge_taxes value for order."""
    tax_configuration, country_tax_configuration = _get_tax_configuration_for_order(
        order
    )
    return get_charge_taxes(tax_configuration, country_tax_configuration)


def get_tax_calculation_strategy_for_order(order: "Order"):
    """Get tax_calculation_strategy value for order."""
    tax_configuration, country_tax_configuration = _get_tax_configuration_for_order(
        order
    )
    return get_tax_calculation_strategy(tax_configuration, country_tax_configuration)


def get_tax_app_identifier_for_order(order: "Order"):
    """Get tax_app_id value for order."""
    tax_configuration, country_tax_configuration = _get_tax_configuration_for_order(
        order
    )
    return get_tax_app_id(tax_configuration, country_tax_configuration)


def get_tax_configuration_for_checkout(
    checkout_info: "CheckoutInfo",
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> tuple["TaxConfiguration", Optional["TaxConfigurationPerCountry"]]:
    tax_configuration = checkout_info.tax_configuration
    country_code = get_active_country(
        checkout_info.channel,
        checkout_info.shipping_address,
        checkout_info.billing_address,
    )
    country_tax_configuration = next(
        (
            tc
            for tc in tax_configuration.country_exceptions.using(
                database_connection_name
            ).all()
            if tc.country.code == country_code
        ),
        None,
    )
    return tax_configuration, country_tax_configuration


def get_charge_taxes_for_checkout(
    checkout_info: "CheckoutInfo",
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    """Get charge_taxes value for checkout."""
    tax_configuration, country_tax_configuration = get_tax_configuration_for_checkout(
        checkout_info, database_connection_name=database_connection_name
    )
    return get_charge_taxes(tax_configuration, country_tax_configuration)


def get_tax_calculation_strategy_for_checkout(
    checkout_info: "CheckoutInfo",
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    """Get tax_calculation_strategy value for checkout."""
    tax_configuration, country_tax_configuration = get_tax_configuration_for_checkout(
        checkout_info, database_connection_name=database_connection_name
    )
    return get_tax_calculation_strategy(tax_configuration, country_tax_configuration)


def get_tax_app_identifier_for_checkout(
    checkout_info: "CheckoutInfo",
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    """Get tax_app_id value for checkout."""
    tax_configuration, country_tax_configuration = get_tax_configuration_for_checkout(
        checkout_info, database_connection_name=database_connection_name
    )
    return get_tax_app_id(tax_configuration, country_tax_configuration)


def should_use_weighted_tax_for_shipping_for_checkout(
    checkout_info: "CheckoutInfo",
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> bool:
    """Get use_weighted_tax_for_shipping value for checkout."""
    tax_configuration, country_tax_configuration = get_tax_configuration_for_checkout(
        checkout_info, database_connection_name=database_connection_name
    )
    return should_use_weighted_tax_for_shipping(
        tax_configuration, country_tax_configuration
    )


def should_use_weighted_tax_for_shipping_for_order(
    order: "Order",
) -> bool:
    """Get use_weighted_tax_for_shipping value for order."""
    tax_configuration, country_tax_configuration = _get_tax_configuration_for_order(
        order
    )
    return should_use_weighted_tax_for_shipping(
        tax_configuration, country_tax_configuration
    )


def _get_weighted_tax_rate_for_shipping(
    lines: list["CheckoutLine"] | list["OrderLine"],
    default_tax_rate: Decimal,
):
    tax_rates_with_weights: dict[Decimal, Decimal] = defaultdict(Decimal)
    for line in lines:
        # tax_rate is stored as fractional values in the database
        tax_rate = line.tax_rate or Decimal(0)
        tax_rates_with_weights[tax_rate * 100] += line.total_price.net.amount
    if not tax_rates_with_weights:
        return default_tax_rate

    total_weight = sum(list(tax_rates_with_weights.values()), Decimal(0))
    if total_weight == 0:
        return default_tax_rate

    weighted_sum = sum(
        [rate * weight for rate, weight in tax_rates_with_weights.items()], Decimal(0)
    )
    return (weighted_sum / total_weight).quantize(Decimal(".0001"))


def get_shipping_tax_rate_for_checkout(
    checkout_info: "CheckoutInfo",
    lines: list["CheckoutLineInfo"],
    default_tax_rate: Decimal,
    country_code: str,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> Decimal:
    should_use_weighted_tax_for_shipping = (
        should_use_weighted_tax_for_shipping_for_checkout(
            checkout_info, database_connection_name=database_connection_name
        )
    )
    if should_use_weighted_tax_for_shipping:
        return _get_weighted_tax_rate_for_shipping(
            [line_info.line for line_info in lines], default_tax_rate
        )
    shipping_tax_rates: Iterable[TaxClassCountryRate] = []
    if shipping_method := checkout_info.shipping_method:
        # external shipping methods do not have a way to provide tax-class
        tax_class_id = shipping_method.tax_class_id
        if tax_class_id:
            shipping_tax_rates = TaxClassCountryRate.objects.using(
                database_connection_name
            ).filter(tax_class_id=tax_class_id)

    return get_tax_rate_for_country(
        shipping_tax_rates,
        default_tax_rate,
        country_code,
    )


def get_shipping_tax_rate_for_order(
    order: "Order",
    lines: Iterable["OrderLine"],
    default_tax_rate: Decimal,
    country_code: str,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> Decimal:
    should_use_weighted_tax_for_shipping = (
        should_use_weighted_tax_for_shipping_for_order(order)
    )
    if should_use_weighted_tax_for_shipping:
        return _get_weighted_tax_rate_for_shipping(list(lines), default_tax_rate)

    shipping_tax_rate = default_tax_rate

    if order.shipping_tax_class_id:
        shipping_tax_rates = TaxClassCountryRate.objects.using(
            database_connection_name
        ).filter(tax_class_id=order.shipping_tax_class_id)
        shipping_tax_rate = get_tax_rate_for_country(
            tax_class_country_rates=shipping_tax_rates,
            default_tax_rate=default_tax_rate,
            country_code=country_code,
        )
    elif (
        order.shipping_tax_class_name is not None
        and order.shipping_tax_rate is not None
    ):
        # Use order.shipping_tax_rate if it was ever set before (it's non-null now and
        # the name is non-null). This is a valid case when recalculating shipping price
        # and the tax class is null, because it was removed from the system.
        shipping_tax_rate = denormalize_tax_rate_from_db(order.shipping_tax_rate)

    return shipping_tax_rate


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


def get_tax_rate_for_country(
    tax_class_country_rates: Iterable["TaxClassCountryRate"],
    default_tax_rate: Decimal,
    country_code: str,
) -> Decimal:
    """Get tax rate for provided country code.

    Function returns the tax rate for provided country code. If not found, the default
    one will be returned.
    `tax_class_country_rates` is the iterable set of rates assigned to single
    `TaxClass`.
    """
    tax_rate = default_tax_rate
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
