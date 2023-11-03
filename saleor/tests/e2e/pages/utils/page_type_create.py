from ...utils import get_graphql_content

PAGE_TYPE_CREATE_MUTATION = """
mutation PageTypeCreate($input: PageTypeCreateInput!) {
  pageTypeCreate(input: $input) {
    errors {
      field
      message
      code
    }
    pageType {
      id
      name
      slug
      attributes{
        id
      }
    }
  }
}
"""


def create_page_type(
    staff_api_client,
    name="test Page Type",
    add_attributes=None,
):
    variables = {"input": {"name": name, "addAttributes": add_attributes}}

    response = staff_api_client.post_graphql(
        PAGE_TYPE_CREATE_MUTATION,
        variables,
    )

    content = get_graphql_content(response)

    data = content["data"]["pageTypeCreate"]
    errors = data["errors"]
    assert errors == []

    page = data["pageType"]
    assert page["id"] is not None

    return page
