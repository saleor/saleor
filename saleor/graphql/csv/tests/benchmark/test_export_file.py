import pytest

from ....tests.utils import get_graphql_content

EXPORT_FILES_QUERY = """
    query ExportFiles {
      exportFiles(first:100) {
        edges {
          node {
            events {
              id
            }
          }
        }
      }
    }
"""


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_export_file_events(
    export_file_with_events,
    staff_api_client,
    permission_manage_products,
):
    # when
    response = staff_api_client.post_graphql(
        EXPORT_FILES_QUERY,
        {},
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["exportFiles"]["edges"]) == 1
    assert len(content["data"]["exportFiles"]["edges"][0]["node"]["events"]) == 10
