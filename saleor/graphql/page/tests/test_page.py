import json

import graphene
import pytest
from django.utils import timezone
from django.utils.text import slugify
from freezegun import freeze_time

from ....page.error_codes import PageErrorCode
from ....page.models import Page
from ...tests.utils import get_graphql_content

PAGE_QUERY = """
    query PageQuery($id: ID, $slug: String) {
        page(id: $id, slug: $slug) {
            title
            slug
            pageType {
                id
            }
            attributes {
                attribute {
                    slug
                }
                values {
                    slug
                }
            }
        }
    }
"""


def test_query_published_page(user_api_client, page):
    page.is_published = True
    page.save()

    page_type = page.page_type

    assert page.attributes.count() == 1
    page_attr_assigned = page.attributes.first()
    page_attr = page_attr_assigned.attribute

    assert page_attr_assigned.values.count() == 1
    page_attr_value = page_attr_assigned.values.first()

    # query by ID
    variables = {"id": graphene.Node.to_global_id("Page", page.id)}
    response = user_api_client.post_graphql(PAGE_QUERY, variables)
    content = get_graphql_content(response)
    page_data = content["data"]["page"]
    assert page_data["title"] == page.title
    assert page_data["slug"] == page.slug
    assert page_data["pageType"]["id"] == graphene.Node.to_global_id(
        "PageType", page.page_type.pk
    )

    expected_attributes = []
    for attr in page_type.page_attributes.all():
        values = [{"slug": page_attr_value.slug}] if attr.slug == page_attr.slug else []
        expected_attributes.append({"attribute": {"slug": attr.slug}, "values": values})

    for attr_data in page_data["attributes"]:
        assert attr_data in expected_attributes

    # query by slug
    variables = {"slug": page.slug}
    response = user_api_client.post_graphql(PAGE_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["page"] is not None


def test_customer_query_unpublished_page(user_api_client, page):
    page.is_published = False
    page.save()

    # query by ID
    variables = {"id": graphene.Node.to_global_id("Page", page.id)}
    response = user_api_client.post_graphql(PAGE_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["page"] is None

    # query by slug
    variables = {"slug": page.slug}
    response = user_api_client.post_graphql(PAGE_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["page"] is None


def test_staff_query_unpublished_page(staff_api_client, page, permission_manage_pages):
    page.is_published = False
    page.save()

    # query by ID
    variables = {"id": graphene.Node.to_global_id("Page", page.id)}
    response = staff_api_client.post_graphql(PAGE_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["page"] is None
    # query by slug
    variables = {"slug": page.slug}
    response = staff_api_client.post_graphql(PAGE_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["page"] is None

    # query by ID with page permissions
    variables = {"id": graphene.Node.to_global_id("Page", page.id)}
    response = staff_api_client.post_graphql(
        PAGE_QUERY,
        variables,
        permissions=[permission_manage_pages],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    assert content["data"]["page"] is not None
    # query by slug with page permissions
    variables = {"slug": page.slug}
    response = staff_api_client.post_graphql(
        PAGE_QUERY,
        variables,
        permissions=[permission_manage_pages],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    assert content["data"]["page"] is not None


CREATE_PAGE_MUTATION = """
    mutation CreatePage(
            $slug: String, $title: String, $content: String, $pageType: ID!
            $contentJson: JSONString, $isPublished: Boolean,
            $attributes: [AttributeValueInput!]) {
        pageCreate(
                input: {
                    slug: $slug, title: $title, pageType: $pageType
                    content: $content, contentJson: $contentJson
                    isPublished: $isPublished, attributes: $attributes}) {
            page {
                id
                title
                content
                contentJson
                slug
                isPublished
                publicationDate
                pageType {
                    id
                }
                attributes {
                    attribute {
                        slug
                    }
                    values {
                        slug
                    }
                }
            }
            pageErrors {
                field
                code
                message
                attributes
            }
        }
    }
"""


@freeze_time("2020-03-18 12:00:00")
def test_page_create_mutation(staff_api_client, permission_manage_pages, page_type):
    page_slug = "test-slug"
    page_content = "test content"
    page_content_json = json.dumps({"content": "test content"})
    page_title = "test title"
    page_is_published = True
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    # Default attributes defined in product_type fixture
    tag_attr = page_type.page_attributes.get(name="tag")
    tag_value_slug = tag_attr.values.first().slug
    tag_attr_id = graphene.Node.to_global_id("Attribute", tag_attr.id)

    # Add second attribute
    size_attr = page_type.page_attributes.get(name="Page size")
    size_attr_id = graphene.Node.to_global_id("Attribute", size_attr.id)
    non_existent_attr_value = "New value"

    # test creating root page
    variables = {
        "title": page_title,
        "content": page_content,
        "contentJson": page_content_json,
        "isPublished": page_is_published,
        "slug": page_slug,
        "pageType": page_type_id,
        "attributes": [
            {"id": tag_attr_id, "values": [tag_value_slug]},
            {"id": size_attr_id, "values": [non_existent_attr_value]},
        ],
    }

    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    assert data["pageErrors"] == []
    assert data["page"]["title"] == page_title
    assert data["page"]["content"] == page_content
    assert data["page"]["contentJson"] == page_content_json
    assert data["page"]["slug"] == page_slug
    assert data["page"]["isPublished"] == page_is_published
    assert data["page"]["publicationDate"] == "2020-03-18"
    assert data["page"]["pageType"]["id"] == page_type_id
    values = (
        data["page"]["attributes"][0]["values"][0]["slug"],
        data["page"]["attributes"][1]["values"][0]["slug"],
    )
    assert slugify(non_existent_attr_value) in values
    assert tag_value_slug in values


def test_page_create_required_fields(
    staff_api_client, permission_manage_pages, page_type
):
    variables = {"pageType": graphene.Node.to_global_id("PageType", page_type.pk)}
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)
    errors = content["data"]["pageCreate"]["pageErrors"]

    assert len(errors) == 1
    assert errors[0]["field"] == "title"
    assert errors[0]["code"] == PageErrorCode.REQUIRED.name


def test_create_default_slug(staff_api_client, permission_manage_pages, page_type):
    # test creating root page
    title = "Spanish inquisition"
    variables = {
        "title": title,
        "pageType": graphene.Node.to_global_id("PageType", page_type.pk),
    }
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    assert not data["pageErrors"]
    assert data["page"]["title"] == title
    assert data["page"]["slug"] == slugify(title)


def test_page_create_mutation_missing_required_attributes(
    staff_api_client, permission_manage_pages, page_type
):
    # given
    page_slug = "test-slug"
    page_content = "test content"
    page_content_json = json.dumps({"content": "test content"})
    page_title = "test title"
    page_is_published = True
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    # Default attributes defined in product_type fixture
    tag_attr = page_type.page_attributes.get(name="tag")
    tag_value_slug = tag_attr.values.first().slug
    tag_attr_id = graphene.Node.to_global_id("Attribute", tag_attr.id)

    # Add second attribute
    size_attr = page_type.page_attributes.get(name="Page size")
    size_attr.value_required = True
    size_attr.save(update_fields=["value_required"])

    # test creating root page
    variables = {
        "title": page_title,
        "content": page_content,
        "contentJson": page_content_json,
        "isPublished": page_is_published,
        "slug": page_slug,
        "pageType": page_type_id,
        "attributes": [{"id": tag_attr_id, "values": [tag_value_slug]}],
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    errors = data["pageErrors"]

    assert not data["page"]
    assert len(errors) == 1
    assert errors[0]["field"] == "attributes"
    assert errors[0]["code"] == PageErrorCode.REQUIRED.name
    assert errors[0]["attributes"] == [
        graphene.Node.to_global_id("Attribute", size_attr.pk)
    ]


def test_page_create_mutation_empty_attribute_value(
    staff_api_client, permission_manage_pages, page_type
):
    # given
    page_slug = "test-slug"
    page_content = "test content"
    page_content_json = json.dumps({"content": "test content"})
    page_title = "test title"
    page_is_published = True
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    # Default attributes defined in product_type fixture
    tag_attr = page_type.page_attributes.get(name="tag")
    tag_attr_id = graphene.Node.to_global_id("Attribute", tag_attr.id)

    # test creating root page
    variables = {
        "title": page_title,
        "content": page_content,
        "contentJson": page_content_json,
        "isPublished": page_is_published,
        "slug": page_slug,
        "pageType": page_type_id,
        "attributes": [{"id": tag_attr_id, "values": ["  "]}],
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    errors = data["pageErrors"]

    assert not data["page"]
    assert len(errors) == 1
    assert errors[0]["field"] == "attributes"
    assert errors[0]["code"] == PageErrorCode.REQUIRED.name
    assert errors[0]["attributes"] == [
        graphene.Node.to_global_id("Attribute", tag_attr.pk)
    ]


def test_page_delete_mutation(staff_api_client, page, permission_manage_pages):
    query = """
        mutation DeletePage($id: ID!) {
            pageDelete(id: $id) {
                page {
                    title
                    id
                }
                pageErrors {
                    field
                    code
                    message
                }
              }
            }
    """
    variables = {"id": graphene.Node.to_global_id("Page", page.id)}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)
    data = content["data"]["pageDelete"]
    assert data["page"]["title"] == page.title
    with pytest.raises(page._meta.model.DoesNotExist):
        page.refresh_from_db()


UPDATE_PAGE_MUTATION = """
    mutation updatePage(
        $id: ID!,
        $slug: String,
        $is_published: Boolean!,
        $attributes: [AttributeValueInput!]
    ) {
        pageUpdate(
            id: $id, input: {
                slug: $slug, isPublished: $is_published, attributes: $attributes
            }
        ) {
            page {
                id
                title
                slug
                isPublished
                publicationDate
                attributes {
                    attribute {
                        slug
                    }
                    values {
                        slug
                    }
                }
            }
            pageErrors {
                field
                code
                message
            }
        }
    }
"""


def test_update_page(staff_api_client, permission_manage_pages, page):
    # given
    query = UPDATE_PAGE_MUTATION

    page_type = page.page_type
    tag_attr = page_type.page_attributes.get(name="tag")
    tag_attr_id = graphene.Node.to_global_id("Attribute", tag_attr.id)
    new_value = "Rainbow"

    page_title = page.title
    new_slug = "new-slug"
    assert new_slug != page.slug

    page_id = graphene.Node.to_global_id("Page", page.id)

    variables = {
        "id": page_id,
        "slug": new_slug,
        "is_published": True,
        "attributes": [{"id": tag_attr_id, "values": [new_value]}],
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageUpdate"]

    assert not data["pageErrors"]
    assert data["page"]["title"] == page_title
    assert data["page"]["slug"] == new_slug

    expected_attributes = []
    page_attr = page.attributes.all()
    for attr in page_type.page_attributes.all():
        if attr.slug != tag_attr.slug:
            values = [
                {"slug": slug}
                for slug in page_attr.filter(assignment__attribute=attr).values_list(
                    "values__slug", flat=True
                )
            ]
        else:
            values = [{"slug": slugify(new_value)}]
        attr_data = {
            "attribute": {"slug": attr.slug},
            "values": values,
        }
        expected_attributes.append(attr_data)

    attributes = data["page"]["attributes"]
    assert len(attributes) == len(expected_attributes)
    for attr_data in attributes:
        assert attr_data in expected_attributes


@freeze_time("2020-03-18 12:00:00")
def test_public_page_sets_publication_date(
    staff_api_client, permission_manage_pages, page_type
):
    data = {
        "slug": "test-url",
        "title": "Test page",
        "content": "test content",
        "is_published": False,
        "page_type": page_type,
    }
    page = Page.objects.create(**data)
    page_id = graphene.Node.to_global_id("Page", page.id)
    variables = {"id": page_id, "is_published": True, "slug": page.slug}
    response = staff_api_client.post_graphql(
        UPDATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)
    data = content["data"]["pageUpdate"]

    assert not data["pageErrors"]
    assert data["page"]["isPublished"] is True
    assert data["page"]["publicationDate"] == "2020-03-18"


@pytest.mark.parametrize("slug_value", [None, ""])
def test_update_page_blank_slug_value(
    staff_api_client, permission_manage_pages, page, slug_value
):
    query = UPDATE_PAGE_MUTATION
    assert slug_value != page.slug

    page_id = graphene.Node.to_global_id("Page", page.id)
    variables = {"id": page_id, "slug": slug_value, "is_published": True}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)
    errors = content["data"]["pageUpdate"]["pageErrors"]

    assert len(errors) == 1
    assert errors[0]["field"] == "slug"
    assert errors[0]["code"] == PageErrorCode.REQUIRED.name


@pytest.mark.parametrize("slug_value", [None, ""])
def test_update_page_with_title_value_and_without_slug_value(
    staff_api_client, permission_manage_pages, page, slug_value
):
    query = """
        mutation updatePage($id: ID!, $title: String, $slug: String) {
        pageUpdate(id: $id, input: {title: $title, slug: $slug}) {
            page {
                id
                title
                slug
            }
            pageErrors {
                field
                code
                message
            }
        }
    }
    """
    page_id = graphene.Node.to_global_id("Page", page.id)
    variables = {"id": page_id, "title": "test", "slug": slug_value}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)
    errors = content["data"]["pageUpdate"]["pageErrors"]

    assert len(errors) == 1
    assert errors[0]["field"] == "slug"
    assert errors[0]["code"] == PageErrorCode.REQUIRED.name


def test_paginate_pages(user_api_client, page, page_type):
    page.is_published = True
    data_02 = {
        "slug": "test02-url",
        "title": "Test page",
        "content": "test content",
        "is_published": True,
        "page_type": page_type,
    }
    data_03 = {
        "slug": "test03-url",
        "title": "Test page",
        "content": "test content",
        "is_published": True,
        "page_type": page_type,
    }

    Page.objects.create(**data_02)
    Page.objects.create(**data_03)
    query = """
        query PagesQuery {
            pages(first: 2) {
                edges {
                    node {
                        id
                        title
                    }
                }
            }
        }
        """
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    pages_data = content["data"]["pages"]
    assert len(pages_data["edges"]) == 2


MUTATION_PUBLISH_PAGES = """
    mutation publishManyPages($ids: [ID]!, $is_published: Boolean!) {
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


@pytest.mark.parametrize(
    "page_filter, count",
    [
        ({"search": "Page1"}, 1),
        ({"search": "slug_page_2"}, 1),
        ({"search": "test"}, 1),
        ({"search": "slug_"}, 3),
        ({"search": "Page"}, 2),
    ],
)
def test_pages_query_with_filter(
    page_filter, count, staff_api_client, permission_manage_pages, page_type
):
    query = """
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
    Page.objects.create(
        title="Page1",
        slug="slug_page_1",
        content="Content for page 1",
        page_type=page_type,
    )
    Page.objects.create(
        title="Page2",
        slug="slug_page_2",
        content="Content for page 2",
        page_type=page_type,
    )
    Page.objects.create(
        title="About",
        slug="slug_about",
        content="About test content",
        page_type=page_type,
    )
    variables = {"filter": page_filter}
    staff_api_client.user.user_permissions.add(permission_manage_pages)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["pages"]["totalCount"] == count


QUERY_PAGE_WITH_SORT = """
    query ($sort_by: PageSortingInput!) {
        pages(first:5, sortBy: $sort_by) {
            edges{
                node{
                    title
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    "page_sort, result_order",
    [
        ({"field": "TITLE", "direction": "ASC"}, ["About", "Page1", "Page2"]),
        ({"field": "TITLE", "direction": "DESC"}, ["Page2", "Page1", "About"]),
        ({"field": "SLUG", "direction": "ASC"}, ["About", "Page2", "Page1"]),
        ({"field": "SLUG", "direction": "DESC"}, ["Page1", "Page2", "About"]),
        ({"field": "VISIBILITY", "direction": "ASC"}, ["Page2", "About", "Page1"]),
        ({"field": "VISIBILITY", "direction": "DESC"}, ["Page1", "About", "Page2"]),
        ({"field": "CREATION_DATE", "direction": "ASC"}, ["Page1", "About", "Page2"]),
        ({"field": "CREATION_DATE", "direction": "DESC"}, ["Page2", "About", "Page1"]),
        (
            {"field": "PUBLICATION_DATE", "direction": "ASC"},
            ["Page1", "Page2", "About"],
        ),
        (
            {"field": "PUBLICATION_DATE", "direction": "DESC"},
            ["About", "Page2", "Page1"],
        ),
    ],
)
def test_query_pages_with_sort(
    page_sort, result_order, staff_api_client, permission_manage_pages, page_type
):
    with freeze_time("2017-05-31 12:00:01"):
        Page.objects.create(
            title="Page1",
            slug="slug_page_1",
            content="p1",
            is_published=True,
            publication_date=timezone.now().replace(year=2018, month=12, day=5),
            page_type=page_type,
        )
    with freeze_time("2019-05-31 12:00:01"):
        Page.objects.create(
            title="Page2",
            slug="page_2",
            content="p2",
            is_published=False,
            publication_date=timezone.now().replace(year=2019, month=12, day=5),
            page_type=page_type,
        )
    with freeze_time("2018-05-31 12:00:01"):
        Page.objects.create(
            title="About",
            slug="about",
            content="Ab",
            is_published=True,
            page_type=page_type,
        )
    variables = {"sort_by": page_sort}
    staff_api_client.user.user_permissions.add(permission_manage_pages)
    response = staff_api_client.post_graphql(QUERY_PAGE_WITH_SORT, variables)
    content = get_graphql_content(response)
    pages = content["data"]["pages"]["edges"]

    for order, page_name in enumerate(result_order):
        assert pages[order]["node"]["title"] == page_name
