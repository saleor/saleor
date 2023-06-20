from ...utils import get_graphql_content

CATEGORY_CREATE_MUTATION = """
mutation CreateCategory($input: CategoryInput!) {
  categoryCreate(input: $input) {
    errors {
      field
      code
      message
    }
    category {
      id
      name
    }
  }
}
"""


def create_category(
    staff_api_client,
    name="Test category",
):
    variables = {
        "input": {
            "name": name,
        }
    }

    response = staff_api_client.post_graphql(
        CATEGORY_CREATE_MUTATION,
        variables,
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    assert content["data"]["categoryCreate"]["errors"] == []

    data = content["data"]["categoryCreate"]["category"]
    assert data["id"] is not None
    assert data["name"] == name

    return data
