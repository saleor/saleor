from ...utils import get_graphql_content

CATEGORY_COLLECTION_MUTATION = """
mutation CollectionCreate($input: CollectionCreateInput!) {
  collectionCreate(input: $input) {
    errors {
      field
      code
      message
    }
    collection {
      id
      name
      slug
    }
  }
}
"""


def create_collection(
    staff_api_client,
    name="Test collection",
):
    variables = {
        "input": {
            "name": name,
        }
    }

    response = staff_api_client.post_graphql(
        CATEGORY_COLLECTION_MUTATION,
        variables,
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    assert content["data"]["collectionCreate"]["errors"] == []

    data = content["data"]["collectionCreate"]["collection"]
    assert data["id"] is not None
    assert data["name"] == name

    return data
