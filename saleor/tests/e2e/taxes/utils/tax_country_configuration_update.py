from ...utils import get_graphql_content

TAX_COUNTRY_CONFIGURATION_UPDATE_MUTATION = """
mutation TaxCountryConfigurationUpdate($countryCode: CountryCode!,
 $updateTaxClassRates: [TaxClassRateInput!]!) {
  taxCountryConfigurationUpdate(
    countryCode: $countryCode
    updateTaxClassRates: $updateTaxClassRates
  ) {
    errors {
      code
      field
      message
      taxClassIds
    }
    taxCountryConfiguration {
      country{
        code
      }
      taxClassCountryRates{
        country{
          code
        }
        rate
        taxClass{
          id
        }
      }
    }
  }
}

"""


def update_country_tax_rates(
    staff_api_client,
    country_code,
    update_tax_class_rates=[],
):
    variables = {
        "countryCode": country_code,
        "updateTaxClassRates": update_tax_class_rates,
    }

    response = staff_api_client.post_graphql(
        TAX_COUNTRY_CONFIGURATION_UPDATE_MUTATION, variables
    )
    content = get_graphql_content(response)

    assert content["data"]["taxCountryConfigurationUpdate"]["errors"] == []

    data = content["data"]["taxCountryConfigurationUpdate"]["taxCountryConfiguration"]

    return data
