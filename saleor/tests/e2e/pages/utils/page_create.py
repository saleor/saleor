from ...utils import get_graphql_content

PAGE_CREATE_MUTATION = """
mutation PageCreate($input: PageCreateInput!) {
  pageCreate(input: $input) {
    errors {
      field
      message
      code
    }
    page {
      id
      title
      slug
      isPublished
      publishedAt
      attributes{
        attribute{
          id
        }
        values{
          id
          name
          slug
          value
          inputType
          reference
          file{
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
"""


def create_page(
    staff_api_client,
    page_type_id,
    title="test Page",
    is_published=True,
    publication_date=None,
    content=None,
    attributes=None,
):
    variables = {
        "input": {
            "pageType": page_type_id,
            "title": title,
            "content": content,
            "isPublished": is_published,
            "publicationDate": publication_date,
            "attributes": attributes,
        }
    }

    response = staff_api_client.post_graphql(
        PAGE_CREATE_MUTATION,
        variables,
    )

    content = get_graphql_content(response)

    data = content["data"]["pageCreate"]
    errors = data["errors"]
    assert errors == []

    page = data["page"]
    assert page["id"] is not None

    return page
