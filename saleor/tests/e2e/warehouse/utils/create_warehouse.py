from ... import DEFAULT_ADDRESS
from ...utils import get_graphql_content

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


def create_warehouse(
    staff_api_client,
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

    response = staff_api_client.post_graphql(WAREHOUSE_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    assert content["data"]["createWarehouse"]["errors"] == []

    data = content["data"]["createWarehouse"]["warehouse"]
    assert data["id"] is not None
    assert data["name"] == name
    assert data["slug"] == slug

    return data
