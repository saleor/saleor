from ...utils import get_graphql_content

TAX_CLASS_UPDATE_MUTATION = """
mutation taxClassUpdate($id:ID!, $input:TaxClassUpdateInput!){
  taxClassUpdate(id:$id, input:$input) {
    errors {
        field
        message
    }
    taxClass {
        id
        countries {
            country {
                code
                }
                rate
                taxClass { id }
            }
        }
  }
}
"""


def update_tax_class(
    staff_api_client,
    tax_class_id,
    tax_class_update_input,
):
    variables = {"id": tax_class_id, "input": tax_class_update_input}

    response = staff_api_client.post_graphql(TAX_CLASS_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)

    assert content["data"]["taxClassUpdate"]["errors"] == []

    data = content["data"]["taxClassUpdate"]["taxClass"]
    assert data["id"] is not None

    return data
