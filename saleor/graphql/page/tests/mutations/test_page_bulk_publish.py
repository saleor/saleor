import graphene

from .....page.models import Page
from ....tests.utils import get_graphql_content

MUTATION_PUBLISH_PAGES = """
    mutation publishManyPages($ids: [ID!]!, $is_published: Boolean!) {
        pageBulkPublish(ids: $ids, isPublished: $is_published) {
            count
        }
    }
    """


def test_bulk_publish(staff_api_client, page_list_unpublished, permission_manage_pages):
    page_list = page_list_unpublished
    assert not any(page.is_published for page in page_list)

    variables = {
        "ids": [graphene.Node.to_global_id("Page", page.id) for page in page_list],
        "is_published": True,
    }
    response = staff_api_client.post_graphql(
        MUTATION_PUBLISH_PAGES, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)
    page_list = Page.objects.filter(id__in=[page.pk for page in page_list])

    assert content["data"]["pageBulkPublish"]["count"] == len(page_list)
    assert all(page.is_published for page in page_list)


def test_bulk_unpublish(staff_api_client, page_list, permission_manage_pages):
    assert all(page.is_published for page in page_list)
    variables = {
        "ids": [graphene.Node.to_global_id("Page", page.id) for page in page_list],
        "is_published": False,
    }
    response = staff_api_client.post_graphql(
        MUTATION_PUBLISH_PAGES, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)
    page_list = Page.objects.filter(id__in=[page.pk for page in page_list])

    assert content["data"]["pageBulkPublish"]["count"] == len(page_list)
    assert not any(page.is_published for page in page_list)
