from unittest.mock import Mock

from prices import Money, TaxedMoney

from saleor.plugins.manager import PluginsManager
from saleor.product.models import ProductVariant
from saleor.product.utils.availability import get_variant_availability
from tests.api.utils import get_graphql_content

QUERY_GET_VARIANT_PRICING = """
query {
  products(first: 1) {
    edges {
      node {
        variants {
          isAvailable
          pricing {
            onSale

            discount {
              currency
              net {
                amount
              }
            }

            priceUndiscounted {
              currency
              net {
                amount
              }
            }

            price {
              currency
              net {
                amount
              }
            }
          }
        }
      }
    }
  }
}
"""


def test_get_variant_pricing_on_sale(api_client, sale, product):
    price = product.price
    discounted_price = price.amount - sale.value

    response = api_client.post_graphql(QUERY_GET_VARIANT_PRICING, {})
    content = get_graphql_content(response)

    pricing = content["data"]["products"]["edges"][0]["node"]["variants"][0]["pricing"]

    # ensure the availability was correctly retrieved and sent
    assert pricing

    # check availability
    assert pricing["onSale"] is True

    # check the discount
    assert pricing["discount"]["currency"] == price.currency
    assert pricing["discount"]["net"]["amount"] == discounted_price

    # check the undiscounted price
    assert pricing["priceUndiscounted"]["currency"] == price.currency
    assert pricing["priceUndiscounted"]["net"]["amount"] == price.amount

    # check the discounted price
    assert pricing["price"]["currency"] == price.currency
    assert pricing["price"]["net"]["amount"] == discounted_price


def test_get_variant_pricing_not_on_sale(api_client, product):
    response = api_client.post_graphql(QUERY_GET_VARIANT_PRICING, {})
    content = get_graphql_content(response)

    pricing = content["data"]["products"]["edges"][0]["node"]["variants"][0]["pricing"]

    # ensure the availability was correctly retrieved and sent
    assert pricing

    # check availability
    assert pricing["onSale"] is False

    # check the discount
    assert pricing["discount"] is None

    # check the undiscounted price
    assert pricing["priceUndiscounted"]["currency"] == product.price.currency
    assert pricing["priceUndiscounted"]["net"]["amount"] == product.price.amount

    # check the discounted price
    assert pricing["price"]["currency"] == product.price.currency
    assert pricing["price"]["net"]["amount"] == product.price.amount


def test_variant_pricing(variant: ProductVariant, monkeypatch, settings, stock):
    taxed_price = TaxedMoney(Money("10.0", "USD"), Money("12.30", "USD"))
    monkeypatch.setattr(
        PluginsManager, "apply_taxes_to_product", Mock(return_value=taxed_price)
    )

    pricing = get_variant_availability(
        variant=variant, product=variant.product, collections=[], discounts=[]
    )
    assert pricing.price == taxed_price
    assert pricing.price_local_currency is None

    monkeypatch.setattr(
        "django_prices_openexchangerates.models.get_rates",
        lambda c: {"PLN": Mock(rate=2)},
    )

    settings.DEFAULT_COUNTRY = "PL"
    settings.OPENEXCHANGERATES_API_KEY = "fake-key"

    pricing = get_variant_availability(
        variant=variant,
        product=variant.product,
        collections=[],
        discounts=[],
        local_currency="PLN",
        country="US",
    )
    assert pricing.price_local_currency.currency == "PLN"  # type: ignore

    pricing = get_variant_availability(
        variant=variant, product=variant.product, collections=[], discounts=[]
    )
    assert pricing.price.tax.amount
    assert pricing.price_undiscounted.tax.amount
    assert pricing.price_undiscounted.tax.amount
