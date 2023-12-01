from ...utils import get_graphql_content

TAX_CONFIGURATION_UPDATE_MUTATION = """
mutation TaxConfigurationUpdate($id: ID!, $input: TaxConfigurationUpdateInput!) {
  taxConfigurationUpdate(id: $id, input: $input) {
    errors {
      field
      code
      message
      countryCodes
    }
    taxConfiguration {
      id
      channel {
        id
        name
      }
      displayGrossPrices
      pricesEnteredWithTax
      chargeTaxes
      taxCalculationStrategy
      countries {
        country {
          code
        }
        chargeTaxes
        taxCalculationStrategy
        displayGrossPrices
      }
    }
  }
}
"""


def update_tax_configuration(
    staff_api_client,
    tax_config_id,
    charge_taxes=True,
    tax_calculation_strategy="FLAT_RATES",
    display_gross_prices=True,
    prices_entered_with_tax=True,
    update_countries_configuration=[],
    remove_countries_configuration=[],
):
    variables = {
        "id": tax_config_id,
        "input": {
            "chargeTaxes": charge_taxes,
            "taxCalculationStrategy": tax_calculation_strategy,
            "displayGrossPrices": display_gross_prices,
            "pricesEnteredWithTax": prices_entered_with_tax,
            "updateCountriesConfiguration": update_countries_configuration,
            "removeCountriesConfiguration": remove_countries_configuration,
        },
    }

    response = staff_api_client.post_graphql(
        TAX_CONFIGURATION_UPDATE_MUTATION, variables
    )
    content = get_graphql_content(response)

    assert content["data"]["taxConfigurationUpdate"]["errors"] == []

    data = content["data"]["taxConfigurationUpdate"]["taxConfiguration"]
    assert data["id"] is not None

    return data
