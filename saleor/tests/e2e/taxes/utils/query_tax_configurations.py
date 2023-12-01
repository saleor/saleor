from ...utils import get_graphql_content

TAX_CONFIGURATIONS_QUERY = """
query TaxConfigurationsList($first: Int) {
  taxConfigurations(first: $first) {
    edges {
      node {
        id
        channel {
          id
          slug
        }
        displayGrossPrices
        pricesEnteredWithTax
        chargeTaxes
        taxCalculationStrategy
      }
    }
  }
}

"""


def get_tax_configurations(
    staff_api_client,
    first=10,
):
    variables = {"first": 10}

    response = staff_api_client.post_graphql(TAX_CONFIGURATIONS_QUERY, variables)
    content = get_graphql_content(response)

    return content["data"]["taxConfigurations"]["edges"]
