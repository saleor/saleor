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
    staff_api_client,
    input_type="DROPDOWN",
    name="Color",
    slug="color",
    type="PRODUCT_TYPE",
    value_required=True,
    is_variant_only=False,
    values=None,
    unit=None,
    entityType=None,
):
    variables = {
        "input": {
            "inputType": input_type,
            "name": name,
            "slug": slug,
            "type": type,
            "valueRequired": value_required,
            "isVariantOnly": is_variant_only,
            "values": values,
            "unit": unit,
            "entityType": entityType,
        }
    }

    response = staff_api_client.post_graphql(
        ATTRIBUTE_CREATE_MUTATION,
        variables,
    )
    content = get_graphql_content(response)

    assert content["data"]["attributeCreate"]["errors"] == []

    data = content["data"]["attributeCreate"]["attribute"]
    assert data["id"] is not None
    return data
