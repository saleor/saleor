from ...utils import get_graphql_content

ATTRIBUTE_BULK_CREATE_MUTATION = """
mutation AttributeBulkCreate($attributes: [AttributeCreateInput!]!) {
  attributeBulkCreate(attributes: $attributes) {
    results {
      errors {
        path
        message
        code
      }
      attribute {
        id
        name
        slug
        choices(first: 10) {
          edges {
            node {
              id
              name
              slug
              value
              inputType
              reference
              file {
                url
                contentType
              }
              richText
              plainText
              boolean
              date
              dateTime
            }
          }
        }
      }
    }
    count
  }
}
"""


def bulk_create_attributes(
    staff_api_client,
    attributes=None,
):
    variables = {"attributes": attributes}

    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_CREATE_MUTATION,
        variables,
    )
    content = get_graphql_content(response)

    assert content["data"]["attributeBulkCreate"]["results"][0]["errors"] == []

    data = content["data"]["attributeBulkCreate"]

    return data
