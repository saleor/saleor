from ...utils import get_graphql_content

WAREHOUSE_UPDATE_MUTATION = """
mutation updateWarehouse($id: ID! $input: WarehouseUpdateInput!) {
  updateWarehouse(id: $id, input: $input) {
    errors {
      message
      field
      code
    }
    warehouse {
      id
      name
      slug
      clickAndCollectOption
      isPrivate
    }
  }
}
"""


def update_warehouse(
    staff_api_client,
    warehouse_id,
    is_private=False,
    click_and_collect_option="DISABLED",
):
    variables = {
        "id": warehouse_id,
        "input": {
            "isPrivate": is_private,
            "clickAndCollectOption": click_and_collect_option,
        },
    }
    response = staff_api_client.post_graphql(WAREHOUSE_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)

    assert content["data"]["updateWarehouse"]["errors"] == []
    data = content["data"]["updateWarehouse"]["warehouse"]
    assert data["isPrivate"] == is_private
    assert data["clickAndCollectOption"] == click_and_collect_option

    return data
