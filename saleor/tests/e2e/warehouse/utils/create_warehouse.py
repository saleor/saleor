import uuid

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
      isPrivate
      shippingZones(first: 10) {
        edges {
          node {
            id
            countries {
              code
            }
          }
        }
      }
      clickAndCollectOption
    }
  }
}
"""


def create_warehouse(
    staff_api_client,
    name="Test warehouse",
    slug=f"warehouse_slug_{uuid.uuid4()}",
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
