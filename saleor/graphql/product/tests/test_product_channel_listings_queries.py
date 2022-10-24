from decimal import Decimal
from unittest import mock

import graphene
import pytest

from ....tax import TaxCalculationStrategy
from ....tax.models import TaxClassCountryRate, TaxConfigurationPerCountry
from ....tax.utils import get_display_gross_prices
from ....warehouse.models import Warehouse
from ...tests.utils import get_graphql_content

TAX_RATE_DE = 19
TAX_RATE_PL = 23

QUERY_PRICING_ON_PRODUCT_CHANNEL_LISTING = """
fragment Pricing on ProductPricingInfo {
  priceRangeUndiscounted {
    start {
      gross {
        amount
        currency
      }
    }
  }
  displayGrossPrices
}
query FetchProduct($id: ID, $channel: String, $address: AddressInput) {
  product(id: $id, channel: $channel) {
    id
    pricing(address: $address) {
      ...Pricing
    }
    channelListings {
      channel {
        slug
      }
      pricing(address: $address) {
        ...Pricing
      }
    }
  }
}
"""


def test_product_channel_listing_pricing_field(
    address_usa,
    staff_api_client,
    permission_manage_products,
    channel_USD,
    product,
):
    # given

    # Changing the address of a warehouse used by the product to address_usa, so that
    # we can query pricing in two countries: US and PL.
    warehouse = Warehouse.objects.first()
    warehouse.address = address_usa
    warehouse.save()

    country = "PL"
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "channel": channel_USD.slug,
        "address": {"country": country},
    }
    product.channel_listings.exclude(channel__slug=channel_USD.slug).delete()

    tax_config = channel_USD.tax_configuration
    tax_config_country = tax_config.country_exceptions.get(country=country)

    # when
    response = staff_api_client.post_graphql(
        QUERY_PRICING_ON_PRODUCT_CHANNEL_LISTING,
        variables=variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    product_data = content["data"]["product"]
    product_channel_listing_data = product_data["channelListings"][0]
    assert product_data["pricing"] == product_channel_listing_data["pricing"]
    assert product_data["pricing"]["displayGrossPrices"] == get_display_gross_prices(
        tax_config, tax_config_country
    )


QUERY_PRICING_ON_PRODUCT_CHANNEL_LISTING_NO_ADDRESS = """
fragment Pricing on ProductPricingInfo {
  priceRangeUndiscounted {
    start {
      gross {
        amount
        currency
      }
    }
  }
}
query FetchProduct($id: ID, $channel: String) {
  product(id: $id, channel: $channel) {
    id
    pricing {
      ...Pricing
    }
    channelListings {
      pricing {
        ...Pricing
      }
    }
  }
}
"""


@mock.patch("saleor.graphql.product.types.products.get_tax_rate_for_tax_class")
def test_product_channel_listing_pricing_field_no_address(
    mock_get_tax_rate_for_tax_class,
    staff_api_client,
    permission_manage_products,
    channel_USD,
    product,
):
    # given
    channel_USD.default_country = "FR"
    channel_USD.save()
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "channel": channel_USD.slug,
    }
    product.channel_listings.exclude(channel__slug=channel_USD.slug).delete()

    # when
    staff_api_client.post_graphql(
        QUERY_PRICING_ON_PRODUCT_CHANNEL_LISTING_NO_ADDRESS,
        variables=variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )

    # then
    assert (
        mock_get_tax_rate_for_tax_class.call_args[0][3] == channel_USD.default_country
    )


FRAGMENT_PRICE = """
  fragment Price on TaxedMoney {
    gross {
      amount
    }
    net {
      amount
    }
    tax {
      amount
    }
  }
"""


FRAGMENT_PRICING = (
    """
  fragment Pricing on ProductPricingInfo {
    priceRange {
      start {
        ...Price
      }
      stop {
        ...Price
      }
    }
    priceRangeUndiscounted {
      start {
        ...Price
      }
      stop {
        ...Price
      }
    }
  }
"""
    + FRAGMENT_PRICE
)


QUERY_PRODUCT_PRICING = (
    """
  query Product($id: ID!, $channel: String!) {
    product(id: $id, channel: $channel) {
      channelListings {
        channel {
          slug
        }
        pricingPL: pricing(address: { country: PL }) {
        ...Pricing
        }
        pricingDE: pricing(address: { country: DE }) {
        ...Pricing
        }
        pricing: pricing {
        ...Pricing
        }
      }
    }
  }
"""
    + FRAGMENT_PRICING
)


def _enable_flat_rates(channel, prices_entered_with_tax):
    tc = channel.tax_configuration
    tc.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES
    tc.prices_entered_with_tax = prices_entered_with_tax
    tc.charge_taxes = True
    tc.country_exceptions.all().delete()
    tc.country_exceptions.create(
        country="PL",
        charge_taxes=True,
        tax_calculation_strategy=TaxCalculationStrategy.FLAT_RATES,
    )
    tc.country_exceptions.create(
        country="DE",
        charge_taxes=True,
        tax_calculation_strategy=TaxCalculationStrategy.FLAT_RATES,
    )
    tc.save()


def _configure_tax_rates(product):
    product.tax_class.country_rates.all().delete()
    product.tax_class.country_rates.create(country="PL", rate=TAX_RATE_PL)
    product.tax_class.country_rates.create(country="DE", rate=TAX_RATE_DE)


@pytest.mark.parametrize(
    "net_PL, gross_PL, net_DE, gross_DE, prices_entered_with_tax",
    [
        (40.65, 50.00, 42.02, 50.00, True),
        (50.00, 61.50, 50.00, 59.50, False),
    ],
)
def test_product_pricing(
    product_available_in_many_channels,
    channel_PLN,
    staff_api_client,
    net_PL,
    gross_PL,
    net_DE,
    gross_DE,
    prices_entered_with_tax,
    permission_manage_products,
):
    # given
    product = product_available_in_many_channels
    _enable_flat_rates(channel_PLN, prices_entered_with_tax)
    _configure_tax_rates(product)

    # when
    variables = {
        "id": graphene.Node.to_global_id("Product", product.id),
        "channel": channel_PLN.slug,
    }
    response = staff_api_client.post_graphql(
        QUERY_PRODUCT_PRICING,
        variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    data = None
    for channel_data in content["data"]["product"]["channelListings"]:
        if channel_data["channel"]["slug"] == channel_PLN.slug:
            data = channel_data

    price_range_PL = data["pricingPL"]["priceRange"]
    price_range_undiscounted_PL = data["pricingPL"]["priceRangeUndiscounted"]
    assert price_range_PL["start"]["net"]["amount"] == net_PL
    assert price_range_PL["start"]["gross"]["amount"] == gross_PL
    assert price_range_PL["stop"]["net"]["amount"] == net_PL
    assert price_range_PL["stop"]["gross"]["amount"] == gross_PL
    assert price_range_undiscounted_PL["start"]["net"]["amount"] == net_PL
    assert price_range_undiscounted_PL["start"]["gross"]["amount"] == gross_PL
    assert price_range_undiscounted_PL["stop"]["net"]["amount"] == net_PL
    assert price_range_undiscounted_PL["stop"]["gross"]["amount"] == gross_PL

    price_range_DE = data["pricingDE"]["priceRange"]
    price_range_undiscounted_DE = data["pricingDE"]["priceRangeUndiscounted"]
    assert price_range_DE["start"]["net"]["amount"] == net_DE
    assert price_range_DE["start"]["gross"]["amount"] == gross_DE
    assert price_range_DE["stop"]["net"]["amount"] == net_DE
    assert price_range_DE["stop"]["gross"]["amount"] == gross_DE
    assert price_range_undiscounted_DE["start"]["net"]["amount"] == net_DE
    assert price_range_undiscounted_DE["start"]["gross"]["amount"] == gross_DE
    assert price_range_undiscounted_DE["stop"]["net"]["amount"] == net_DE
    assert price_range_undiscounted_DE["stop"]["gross"]["amount"] == gross_DE


def test_product_pricing_default_country_default_rate(
    product_available_in_many_channels,
    channel_PLN,
    staff_api_client,
    permission_manage_products,
):
    # given
    product = product_available_in_many_channels
    _enable_flat_rates(channel_PLN, True)
    TaxClassCountryRate.objects.all().delete()
    TaxClassCountryRate.objects.create(
        country=channel_PLN.default_country, rate=TAX_RATE_PL
    )

    # when
    variables = {
        "id": graphene.Node.to_global_id("Product", product.id),
        "channel": channel_PLN.slug,
    }
    response = staff_api_client.post_graphql(
        QUERY_PRODUCT_PRICING,
        variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    data = None
    for channel_data in content["data"]["product"]["channelListings"]:
        if channel_data["channel"]["slug"] == channel_PLN.slug:
            data = channel_data

    variant = product.variants.first()
    channel_listing = variant.channel_listings.filter(channel_id=channel_PLN.id).first()
    gross = channel_listing.price_amount.quantize(Decimal(".01"))
    net = (gross / Decimal(1 + TAX_RATE_PL / 100)).quantize(Decimal(".01"))
    gross = float(gross)
    net = float(net)

    price_range = data["pricing"]["priceRange"]
    price_range_undiscounted = data["pricing"]["priceRangeUndiscounted"]

    assert price_range["start"]["net"]["amount"] == net
    assert price_range["start"]["gross"]["amount"] == gross
    assert price_range["stop"]["net"]["amount"] == net
    assert price_range["stop"]["gross"]["amount"] == gross
    assert price_range_undiscounted["start"]["net"]["amount"] == net
    assert price_range_undiscounted["start"]["gross"]["amount"] == gross
    assert price_range_undiscounted["stop"]["net"]["amount"] == net
    assert price_range_undiscounted["stop"]["gross"]["amount"] == gross


def test_product_pricing_use_tax_class_from_product_type(
    product_available_in_many_channels,
    channel_PLN,
    staff_api_client,
    permission_manage_products,
):
    # given
    product = product_available_in_many_channels
    _enable_flat_rates(channel_PLN, True)
    TaxClassCountryRate.objects.all().delete()
    product.tax_class = None
    product.save(update_fields=["tax_class"])
    product.product_type.tax_class.country_rates.create(
        country=channel_PLN.default_country, rate=TAX_RATE_PL
    )

    # when
    variables = {
        "id": graphene.Node.to_global_id("Product", product.id),
        "channel": channel_PLN.slug,
    }
    response = staff_api_client.post_graphql(
        QUERY_PRODUCT_PRICING,
        variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    variant = product.variants.first()
    channel_listing = variant.channel_listings.filter(channel_id=channel_PLN.id).first()
    gross = channel_listing.price_amount.quantize(Decimal(".01"))
    net = (gross / Decimal(1 + TAX_RATE_PL / 100)).quantize(Decimal(".01"))
    gross = float(gross)
    net = float(net)

    data = None
    for channel_data in content["data"]["product"]["channelListings"]:
        if channel_data["channel"]["slug"] == channel_PLN.slug:
            data = channel_data

    price_range_PL = data["pricingPL"]["priceRange"]
    price_range_undiscounted_PL = data["pricingPL"]["priceRangeUndiscounted"]
    assert price_range_PL["start"]["net"]["amount"] == net
    assert price_range_PL["start"]["gross"]["amount"] == gross
    assert price_range_PL["stop"]["net"]["amount"] == net
    assert price_range_PL["stop"]["gross"]["amount"] == gross
    assert price_range_undiscounted_PL["start"]["net"]["amount"] == net
    assert price_range_undiscounted_PL["start"]["gross"]["amount"] == gross
    assert price_range_undiscounted_PL["stop"]["net"]["amount"] == net
    assert price_range_undiscounted_PL["stop"]["gross"]["amount"] == gross


def test_product_pricing_no_flat_rates_in_one_country(
    product_available_in_many_channels,
    channel_PLN,
    staff_api_client,
    permission_manage_products,
):
    # given
    product = product_available_in_many_channels
    _enable_flat_rates(channel_PLN, True)
    _configure_tax_rates(product)
    TaxConfigurationPerCountry.objects.filter(country="PL").update(
        tax_calculation_strategy=None
    )

    # when
    variables = {
        "id": graphene.Node.to_global_id("Product", product.id),
        "channel": channel_PLN.slug,
    }
    response = staff_api_client.post_graphql(
        QUERY_PRODUCT_PRICING,
        variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    variant = product.variants.first()
    channel_listing = variant.channel_listings.filter(channel_id=channel_PLN.id).first()
    price_pl = float(channel_listing.price_amount.quantize(Decimal(".01")))
    gross_de = channel_listing.price_amount.quantize(Decimal(".01"))
    net_de = (gross_de / Decimal(1 + TAX_RATE_DE / 100)).quantize(Decimal(".01"))
    gross_de = float(gross_de)
    net_de = float(net_de)

    data = None
    for channel_data in content["data"]["product"]["channelListings"]:
        if channel_data["channel"]["slug"] == channel_PLN.slug:
            data = channel_data

    price_range_PL = data["pricingPL"]["priceRange"]
    price_range_undiscounted_PL = data["pricingPL"]["priceRangeUndiscounted"]
    assert price_range_PL["start"]["net"]["amount"] == price_pl
    assert price_range_PL["start"]["gross"]["amount"] == price_pl
    assert price_range_PL["stop"]["net"]["amount"] == price_pl
    assert price_range_PL["stop"]["gross"]["amount"] == price_pl
    assert price_range_undiscounted_PL["start"]["net"]["amount"] == price_pl
    assert price_range_undiscounted_PL["start"]["gross"]["amount"] == price_pl
    assert price_range_undiscounted_PL["stop"]["net"]["amount"] == price_pl
    assert price_range_undiscounted_PL["stop"]["gross"]["amount"] == price_pl

    price_range_DE = data["pricingDE"]["priceRange"]
    price_range_undiscounted_DE = data["pricingDE"]["priceRangeUndiscounted"]
    assert price_range_DE["start"]["net"]["amount"] == net_de
    assert price_range_DE["start"]["gross"]["amount"] == gross_de
    assert price_range_DE["stop"]["net"]["amount"] == net_de
    assert price_range_DE["stop"]["gross"]["amount"] == gross_de
    assert price_range_undiscounted_DE["start"]["net"]["amount"] == net_de
    assert price_range_undiscounted_DE["start"]["gross"]["amount"] == gross_de
    assert price_range_undiscounted_DE["stop"]["net"]["amount"] == net_de
    assert price_range_undiscounted_DE["stop"]["gross"]["amount"] == gross_de
