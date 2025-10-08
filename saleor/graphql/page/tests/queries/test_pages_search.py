import pytest

from .....attribute.utils import associate_attribute_values_to_instance
from .....page.models import Page
from .....page.search import update_pages_search_vector
from .....tests.utils import dummy_editorjs
from ....tests.utils import get_graphql_content

QUERY_PAGES_WITH_SEARCH = """
    query ($search: String) {
        pages(first: 5, search:$search) {
            totalCount
            edges {
                node {
                    id
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    ("search", "count"),
    [
        ("Author1", 1),
        ("about", 1),
        ("Author", 2),
    ],
)
def test_pages_query_with_search_by_title(
    search, count, staff_api_client, permission_manage_pages, page_type
):
    # given
    query = QUERY_PAGES_WITH_SEARCH
    pages = Page.objects.bulk_create(
        [
            Page(
                title="Author1",
                slug="slug_author_1",
                content=dummy_editorjs("Content for page 1"),
                page_type=page_type,
            ),
            Page(
                title="Author2",
                slug="slug_author_2",
                content=dummy_editorjs("Content for page 2"),
                page_type=page_type,
            ),
            Page(
                title="About",
                slug="slug_about",
                content=dummy_editorjs("About test content"),
                page_type=page_type,
            ),
        ]
    )
    update_pages_search_vector(pages)
    variables = {"search": search}
    staff_api_client.user.user_permissions.add(permission_manage_pages)

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["pages"]["totalCount"] == count


@pytest.mark.parametrize(
    ("search", "count"),
    [
        ("slug_author_1", 1),
        ("1", 1),
        ("slug_author", 2),
    ],
)
def test_pages_query_with_search_by_slug(
    search, count, staff_api_client, permission_manage_pages, page_type
):
    # given
    query = QUERY_PAGES_WITH_SEARCH
    pages = Page.objects.bulk_create(
        [
            Page(
                title="Author1",
                slug="slug_author_1",
                content=dummy_editorjs("Content for page 1"),
                page_type=page_type,
            ),
            Page(
                title="Author2",
                slug="slug_author_2",
                content=dummy_editorjs("Content for page 2"),
                page_type=page_type,
            ),
            Page(
                title="About",
                slug="slug_about",
                content=dummy_editorjs("About test content"),
                page_type=page_type,
            ),
        ]
    )
    update_pages_search_vector(pages)
    variables = {"search": search}
    staff_api_client.user.user_permissions.add(permission_manage_pages)

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["pages"]["totalCount"] == count


@pytest.mark.parametrize(
    ("search", "count"),
    [
        ("content", 3),
        ("Description", 1),
    ],
)
def test_pages_query_with_search_by_content(
    search, count, staff_api_client, permission_manage_pages, page_type
):
    # given
    query = QUERY_PAGES_WITH_SEARCH
    pages = Page.objects.bulk_create(
        [
            Page(
                title="Author1",
                slug="slug_author_1",
                content=dummy_editorjs("Content for page 1. Description."),
                page_type=page_type,
            ),
            Page(
                title="Author2",
                slug="slug_author_2",
                content=dummy_editorjs("Content for page 2"),
                page_type=page_type,
            ),
            Page(
                title="About",
                slug="slug_about",
                content=dummy_editorjs("About test content"),
                page_type=page_type,
            ),
        ]
    )
    update_pages_search_vector(pages)
    variables = {"search": search}
    staff_api_client.user.user_permissions.add(permission_manage_pages)

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["pages"]["totalCount"] == count


@pytest.mark.parametrize(
    ("search", "count"),
    [
        ("page-type", 2),
        ("page type", 3),
        ("test-page-type", 1),
        ("Example", 2),
    ],
)
def test_pages_query_with_search_by_page_type(
    search,
    count,
    staff_api_client,
    permission_manage_pages,
    page_type_list,
):
    # given
    query = QUERY_PAGES_WITH_SEARCH
    pages = Page.objects.bulk_create(
        [
            Page(
                title="Author1",
                slug="slug_author_1",
                content=dummy_editorjs("Content for page 1. Description."),
                page_type=page_type_list[0],
            ),
            Page(
                title="Author2",
                slug="slug_author_2",
                content=dummy_editorjs("Content for page 2"),
                page_type=page_type_list[1],
            ),
            Page(
                title="About",
                slug="slug_about",
                content=dummy_editorjs("About test content"),
                page_type=page_type_list[2],
            ),
        ]
    )
    update_pages_search_vector(pages)
    variables = {"search": search}
    staff_api_client.user.user_permissions.add(permission_manage_pages)

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["pages"]["totalCount"] == count


@pytest.mark.parametrize(
    ("search", "count"),
    [
        ("10", 2),  # size value
        ("help", 1),  # tag value
    ],
)
def test_pages_query_with_search_by_attributes(
    search,
    count,
    staff_api_client,
    permission_manage_pages,
    page_type_list,
    size_page_attribute,
    tag_page_attribute,
):
    # given
    query = QUERY_PAGES_WITH_SEARCH
    pages = Page.objects.bulk_create(
        [
            Page(
                title="Author1",
                slug="slug_author_1",
                content=dummy_editorjs("Content for page 1. Description."),
                page_type=page_type_list[0],
            ),
            Page(
                title="Author2",
                slug="slug_author_2",
                content=dummy_editorjs("Content for page 2"),
                page_type=page_type_list[1],
            ),
            Page(
                title="About",
                slug="slug_about",
                content=dummy_editorjs("About test content"),
                page_type=page_type_list[2],
            ),
        ]
    )
    for page_type in page_type_list:
        page_type.page_attributes.add(size_page_attribute, tag_page_attribute)

    page_1, _page_2, page_3 = pages
    size_value = size_page_attribute.values.first()
    tag_value = tag_page_attribute.values.last()

    associate_attribute_values_to_instance(
        page_1, {size_page_attribute.id: [size_value]}
    )
    associate_attribute_values_to_instance(
        page_3,
        {size_page_attribute.id: [size_value], tag_page_attribute.id: [tag_value]},
    )

    update_pages_search_vector(pages)
    variables = {"search": search}
    staff_api_client.user.user_permissions.add(permission_manage_pages)

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["pages"]["totalCount"] == count


QUERY_PAGES_WITH_FILTER = """
    query ($filter: PageFilterInput) {
        pages(first: 5, filter:$filter) {
            totalCount
            edges {
                node {
                    id
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    ("page_filter", "count"),
    [
        ({"search": "Author1"}, 1),
        ({"search": "about"}, 1),
        ({"search": "test"}, 3),
        ({"search": "slug"}, 3),
        ({"search": "Author"}, 2),
    ],
)
def test_pages_query_with_filter(
    page_filter, count, staff_api_client, permission_manage_pages, page_type
):
    # given
    query = QUERY_PAGES_WITH_FILTER
    pages = Page.objects.bulk_create(
        [
            Page(
                title="Author1",
                slug="slug_author_1",
                content=dummy_editorjs("Content for page 1"),
                page_type=page_type,
            ),
            Page(
                title="Author2",
                slug="slug_author_2",
                content=dummy_editorjs("Content for page 2"),
                page_type=page_type,
            ),
            Page(
                title="About",
                slug="slug_about",
                content=dummy_editorjs("About test content"),
                page_type=page_type,
            ),
        ]
    )
    update_pages_search_vector(pages)
    variables = {"filter": page_filter}
    staff_api_client.user.user_permissions.add(permission_manage_pages)

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["pages"]["totalCount"] == count
