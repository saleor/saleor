from ...utils import get_graphql_content

ATTRIBUTE_UPDATE_MUTATION = """
    mutation updateAttribute(
        $id: ID!, $input: AttributeUpdateInput!
    ) {
    attributeUpdate(
            id: $id,
            input: $input) {
        errors {
            field
            message
            code
        }
        attribute {
            id
            name
            slug
            unit
            entityType
            referenceTypes {
                ... on ProductType {
                    id
                    slug
                }
                ... on PageType {
                    id
                    slug
                }
            }
            externalReference
            productTypes(first: 10) {
                edges {
                    node {
                        id
                    }
                }
            }
        }
    }
}
"""


def attribute_update(client, attribute_id, input_data):
    """Send a GraphQL mutation to update an attribute."""
    variables = {"id": attribute_id, "input": input_data}

    response = client.post_graphql(
        ATTRIBUTE_UPDATE_MUTATION,
        variables,
    )
    content = get_graphql_content(response)

    assert content["data"]["attributeUpdate"]["errors"] == []
    data = content["data"]["attributeUpdate"]["attribute"]
    assert data["id"] == attribute_id
    return data
