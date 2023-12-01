from ...utils import get_graphql_content

TAX_CLASS_CREATE_MUTATION = """
mutation TaxClassCreate($input: TaxClassCreateInput!) {
  taxClassCreate(input: $input) {
    errors {
      field
      message
      code
    }
    taxClass {
      id
      name
      countries {
        country {
          code
        }
        rate
        taxClass {
          id
        }
      }
    }
  }
}
"""


def create_tax_class(
    staff_api_client,
    tax_class_name="Test Tax Class",
    country_rates=None,
):
    variables = {"input": {"name": tax_class_name, "createCountryRates": country_rates}}

    response = staff_api_client.post_graphql(TAX_CLASS_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    assert content["data"]["taxClassCreate"]["errors"] == []

    data = content["data"]["taxClassCreate"]["taxClass"]
    assert data["id"] is not None

    return data
