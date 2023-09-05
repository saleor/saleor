from ...utils import get_graphql_content

SALE_CREATE_MUTATION = """
mutation createSale($input: SaleInput!) {
  saleCreate(input: $input) {
    errors {
      field
      code
      message
    }
    sale {
      id
      name
      type
      startDate
      endDate
    }
  }
}
"""


def create_sale(
    staff_api_client,
    name="Test sale",
    sale_type="FIXED",
):
    variables = {"input": {"name": name, "type": sale_type}}

    response = staff_api_client.post_graphql(
        SALE_CREATE_MUTATION,
        variables,
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    assert content["data"]["saleCreate"]["errors"] == []

    data = content["data"]["saleCreate"]["sale"]
    assert data["id"] is not None
    assert data["name"] == name
    assert data["type"] == sale_type

    return data
