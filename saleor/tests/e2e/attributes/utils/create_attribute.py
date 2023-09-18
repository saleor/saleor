from ...utils import get_graphql_content

ATTRIBUTE_CREATE_MUTATION = """
mutation AttributeCreate($input: AttributeCreateInput!) {
  attributeCreate(input: $input) {
    attribute {
      id
    }
    errors {
      code
      field
      message
    }
  }
}
"""


def attribute_create(
    e2e_not_logged_api_client,
    input_type="DROPDOWN",
    name="Color",
    slug="color",
    type="PRODUCT_TYPE",
    value_required=True,
):
    variables = {
        "input": {
            "inputType": input_type,
            "name": name,
            "slug": slug,
            "type": type,
            "valueRequired": value_required,
        }
    }

    response = e2e_not_logged_api_client.post_graphql(
        ATTRIBUTE_CREATE_MUTATION,
        variables,
    )
    content = get_graphql_content(response)

    assert content["data"]["attributeCreate"]["errors"] == []

    data = content["data"]["attributeCreate"]["attribute"]
    assert data["id"] is not None
    return data
