import graphene

from ....page.models import Page
from ...tests.utils import get_graphql_content


def test_delete_pages(staff_api_client, page_list, permission_manage_pages):
    query = """
    mutation pageBulkDelete($ids: [ID]!) {
        pageBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {
        "ids": [graphene.Node.to_global_id("Page", page.id) for page in page_list]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)

    assert content["data"]["pageBulkDelete"]["count"] == len(page_list)
    assert not Page.objects.filter(id__in=[page.id for page in page_list]).exists()
