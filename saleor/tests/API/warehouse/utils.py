from ..utils import get_graphql_content

WAREHOUSE_CREATE_MUTATION = """
mutation createWarehouse($input: WarehouseCreateInput!) {
  createWarehouse(input: $input) {
    errors {
      message
      field
      code
    }
    warehouse {
      id
      name
      slug
    }
  }
}
"""


DEFAULT_ADDRESS = {
    "firstName": "John Saleor",
    "lastName": "Doe Mirumee",
    "companyName": "Saleor Commerce",
    "streetAddress1": "	14208 Hawthorne Blvd",
    "streetAddress2": "",
    "postalCode": "90250",
    "country": "US",
    "city": "Hawthorne",
    "countryArea": "CA",
    "phone": "+12025550163",
}


def create_warehouse(
    staff_api_client,
    permissions,
    name="Test warehouse",
    slug="test-slug",
    address=DEFAULT_ADDRESS,
):
    variables = {
        "input": {
            "name": name,
            "slug": slug,
            "address": address,
        }
    }

    response = staff_api_client.post_graphql(
        WAREHOUSE_CREATE_MUTATION, variables, permissions=permissions
    )
    content = get_graphql_content(response)

    assert content["data"]["createWarehouse"]["errors"] == []

    data = content["data"]["createWarehouse"]["warehouse"]
    assert data["id"] is not None
    assert data["name"] == name
    assert data["slug"] == slug

    return data
