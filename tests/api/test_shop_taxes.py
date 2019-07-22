from unittest.mock import patch

import pytest
from django_prices_vatlayer.models import VAT
from django_prices_vatlayer.utils import get_tax_for_rate

from saleor.graphql.core.utils import str_to_enum
from tests.api.utils import get_graphql_content

# FIXME we are going to rewrite tax section. Currently, below tests are connected only
#  with vatlayer. After we introduce approach for taxes and API, we should rebuild this
#  tests.


@pytest.fixture
def tax_rates():
    return {
        "standard_rate": 23,
        "reduced_rates": {
            "pharmaceuticals": 8,
            "medical": 8,
            "passenger transport": 8,
            "newspapers": 8,
            "hotels": 8,
            "restaurants": 8,
            "admission to cultural events": 8,
            "admission to sporting events": 8,
            "admission to entertainment events": 8,
            "foodstuffs": 5,
        },
    }


@pytest.fixture
def taxes(tax_rates):
    taxes = {
        "standard": {
            "value": tax_rates["standard_rate"],
            "tax": get_tax_for_rate(tax_rates),
        }
    }
    if tax_rates["reduced_rates"]:
        taxes.update(
            {
                rate: {
                    "value": tax_rates["reduced_rates"][rate],
                    "tax": get_tax_for_rate(tax_rates, rate),
                }
                for rate in tax_rates["reduced_rates"]
            }
        )
    return taxes


@pytest.fixture
def vatlayer(db, settings, tax_rates, taxes):
    settings.VATLAYER_ACCESS_KEY = "enablevatlayer"
    VAT.objects.create(country_code="PL", data=tax_rates)

    tax_rates_2 = {
        "standard_rate": 19,
        "reduced_rates": {
            "admission to cultural events": 7,
            "admission to entertainment events": 7,
            "books": 7,
            "foodstuffs": 7,
            "hotels": 7,
            "medical": 7,
            "newspapers": 7,
            "passenger transport": 7,
        },
    }
    VAT.objects.create(country_code="DE", data=tax_rates_2)
    return taxes


def test_query_countries_with_tax(user_api_client, vatlayer, tax_rates):
    query = """
    query {
        shop {
            countries {
                code
                vat {
                    standardRate
                    reducedRates {
                        rate
                        rateType
                    }
                }
            }
        }
    }
    """
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    data = content["data"]["shop"]["countries"]
    vat = VAT.objects.first()
    country = next(country for country in data if country["code"] == vat.country_code)
    assert country["vat"]["standardRate"] == tax_rates["standard_rate"]
    rates = {rate["rateType"]: rate["rate"] for rate in country["vat"]["reducedRates"]}
    reduced_rates = {
        str_to_enum(tax_rate): tax_rates["reduced_rates"][tax_rate]
        for tax_rate in tax_rates["reduced_rates"]
    }
    assert rates == reduced_rates


def test_query_default_country_with_tax(user_api_client, settings, vatlayer, tax_rates):
    settings.DEFAULT_COUNTRY = "PL"
    query = """
    query {
        shop {
            defaultCountry {
                code
                vat {
                    standardRate
                }
            }
        }
    }
    """
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    data = content["data"]["shop"]["defaultCountry"]
    assert data["code"] == settings.DEFAULT_COUNTRY
    assert data["vat"]["standardRate"] == tax_rates["standard_rate"]


MUTATION_SHOP_FETCH_TAX_RATES = """
    mutation FetchTaxRates {
        shopFetchTaxRates {
            errors {
                field
                message
            }
        }
    }
    """


def test_shop_fetch_tax_rates_no_api_access_key(
    staff_api_client, permission_manage_settings
):
    staff_api_client.user.user_permissions.add(permission_manage_settings)
    response = staff_api_client.post_graphql(MUTATION_SHOP_FETCH_TAX_RATES)
    content = get_graphql_content(response)
    data = content["data"]["shopFetchTaxRates"]
    error_message = (
        "Could not fetch tax rates. "
        "Make sure you have supplied a valid API Access Key."
    )
    assert data["errors"][0]["message"] == error_message


@patch("saleor.graphql.shop.mutations.call_command")
def test_shop_fetch_tax_rates(
    mock_call_command, staff_api_client, permission_manage_settings, settings
):
    settings.VATLAYER_ACCESS_KEY = "KEY"
    staff_api_client.user.user_permissions.add(permission_manage_settings)
    response = staff_api_client.post_graphql(MUTATION_SHOP_FETCH_TAX_RATES)
    get_graphql_content(response)
    mock_call_command.assert_called_once_with("get_vat_rates")
