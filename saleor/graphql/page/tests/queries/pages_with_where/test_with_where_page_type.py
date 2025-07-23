import graphene

from ......page.models import Page, PageType
from .....tests.utils import get_graphql_content
from .shared import QUERY_PAGES_WITH_WHERE


def test_pages_with_where_page_type_eq(staff_api_client, page_type_list):
    # given
    page = Page.objects.first()
    assigned_page_type = page.page_type
    page_type_id = graphene.Node.to_global_id("PageType", page.page_type.pk)

    pages_for_page_type = Page.objects.filter(page_type=assigned_page_type).count()
    assert PageType.objects.exclude(pk=assigned_page_type.pk).count() != 0
    assert pages_for_page_type != 0

    variables = {"where": {"pageType": {"eq": page_type_id}}}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert len(pages_nodes) == pages_for_page_type


def test_pages_with_where_page_type_one_of(staff_api_client, page_type_list):
    # given
    page = Page.objects.first()
    assigned_page_type = page.page_type
    page_type_id = graphene.Node.to_global_id("PageType", page.page_type.pk)

    pages_for_page_type = Page.objects.filter(page_type=assigned_page_type).count()
    assert PageType.objects.exclude(pk=assigned_page_type.pk).count() != 0
    assert pages_for_page_type != 0

    variables = {"where": {"pageType": {"oneOf": [page_type_id]}}}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert len(pages_nodes) == pages_for_page_type
