import graphene
import pytest
from django.utils import timezone
from freezegun import freeze_time

from .....attribute.models.base import AttributeValue
from .....attribute.utils import associate_attribute_values_to_instance
from .....page.models import Page
from .....tests.utils import dummy_editorjs
from ....tests.utils import get_graphql_content

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
        ({"search": "Page1"}, 2),
        ({"search": "about"}, 1),
        ({"search": "test"}, 1),
        ({"search": "slug"}, 3),
        ({"search": "Page"}, 2),
    ],
)
def test_pages_query_with_filter(
    page_filter, count, staff_api_client, permission_manage_pages, page_type
):
    query = QUERY_PAGES_WITH_FILTER
    Page.objects.create(
        title="Page1",
        slug="slug_page_1",
        content=dummy_editorjs("Content for page 1"),
        page_type=page_type,
    )
    Page.objects.create(
        title="Page2",
        slug="slug_page_2",
        content=dummy_editorjs("Content for page 2"),
        page_type=page_type,
    )
    Page.objects.create(
        title="About",
        slug="slug_about",
        content=dummy_editorjs("About test content"),
        page_type=page_type,
    )
    variables = {"filter": page_filter}
    staff_api_client.user.user_permissions.add(permission_manage_pages)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["pages"]["totalCount"] == count


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
        ("Page1", 2),
        ("about", 1),
        ("test", 1),
        ("slug", 3),
        ("Page", 2),
    ],
)
def test_pages_query_with_search(
    search, count, staff_api_client, permission_manage_pages, page_type
):
    # given
    query = QUERY_PAGES_WITH_SEARCH
    Page.objects.create(
        title="Page1",
        slug="slug_page_1",
        content=dummy_editorjs("Content for page 1"),
        page_type=page_type,
    )
    Page.objects.create(
        title="Page2",
        slug="slug_page_2",
        content=dummy_editorjs("Content for page 2"),
        page_type=page_type,
    )
    Page.objects.create(
        title="About",
        slug="slug_about",
        content=dummy_editorjs("About test content"),
        page_type=page_type,
    )
    variables = {"search": search}
    staff_api_client.user.user_permissions.add(permission_manage_pages)

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["pages"]["totalCount"] == count


def test_pages_query_with_filter_by_page_type(
    staff_api_client, permission_manage_pages, page_type_list
):
    query = QUERY_PAGES_WITH_FILTER
    page_type_ids = [
        graphene.Node.to_global_id("PageType", page_type.id)
        for page_type in page_type_list
    ][:2]

    variables = {"filter": {"pageTypes": page_type_ids}}
    staff_api_client.user.user_permissions.add(permission_manage_pages)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["pages"]["totalCount"] == 2


@pytest.mark.parametrize(
    ("filter_by", "pages_count"),
    [
        ({"slugs": ["test-url-1"]}, 1),
        ({"slugs": ["test-url-1", "test-url-2"]}, 2),
        ({"slugs": []}, 4),
    ],
)
def test_pages_with_filtering(filter_by, pages_count, staff_api_client, page_list):
    # given
    variables = {"filter": filter_by}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_FILTER,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert len(pages_nodes) == pages_count


def test_pages_query_with_filter_by_ids(
    staff_api_client, permission_manage_pages, page_list, page_list_unpublished
):
    query = QUERY_PAGES_WITH_FILTER

    page_ids = [
        graphene.Node.to_global_id("Page", page.pk)
        for page in [page_list[0], page_list_unpublished[-1]]
    ]
    variables = {"filter": {"ids": page_ids}}
    staff_api_client.user.user_permissions.add(permission_manage_pages)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["pages"]["totalCount"] == len(page_ids)


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
    ("page_sort", "result_order"),
    [
        ({"field": "TITLE", "direction": "ASC"}, ["About", "Page1", "Page2"]),
        ({"field": "TITLE", "direction": "DESC"}, ["Page2", "Page1", "About"]),
        ({"field": "SLUG", "direction": "ASC"}, ["About", "Page2", "Page1"]),
        ({"field": "SLUG", "direction": "DESC"}, ["Page1", "Page2", "About"]),
        ({"field": "VISIBILITY", "direction": "ASC"}, ["Page2", "About", "Page1"]),
        ({"field": "VISIBILITY", "direction": "DESC"}, ["Page1", "About", "Page2"]),
        ({"field": "CREATION_DATE", "direction": "ASC"}, ["Page1", "About", "Page2"]),
        ({"field": "CREATION_DATE", "direction": "DESC"}, ["Page2", "About", "Page1"]),
        ({"field": "CREATED_AT", "direction": "ASC"}, ["Page1", "About", "Page2"]),
        ({"field": "CREATED_AT", "direction": "DESC"}, ["Page2", "About", "Page1"]),
        (
            {"field": "PUBLISHED_AT", "direction": "ASC"},
            ["Page1", "Page2", "About"],
        ),
        (
            {"field": "PUBLISHED_AT", "direction": "DESC"},
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
            content=dummy_editorjs("p1."),
            is_published=True,
            published_at=timezone.now().replace(year=2018, month=12, day=5),
            page_type=page_type,
        )
    with freeze_time("2019-05-31 12:00:01"):
        Page.objects.create(
            title="Page2",
            slug="page_2",
            content=dummy_editorjs("p2."),
            is_published=False,
            published_at=timezone.now().replace(year=2019, month=12, day=5),
            page_type=page_type,
        )
    with freeze_time("2018-05-31 12:00:01"):
        Page.objects.create(
            title="About",
            slug="about",
            content=dummy_editorjs("Ab."),
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


PAGES_QUERY = """
    query {
        pages(first: 10) {
            edges {
                node {
                    id
                    title
                    slug
                    pageType {
                        id
                    }
                    content
                    contentJson
                    attributes {
                        attribute {
                            slug
                        }
                        values {
                            id
                            slug
                        }
                    }
                }
            }
        }
    }
"""


def test_query_pages_by_staff(
    staff_api_client, page_list, page, permission_manage_pages
):
    # given
    unpublished_page = page
    unpublished_page.is_published = False
    unpublished_page.save(update_fields=["is_published"])

    page_count = Page.objects.count()

    staff_api_client.user.user_permissions.add(permission_manage_pages)

    # when
    response = staff_api_client.post_graphql(PAGES_QUERY)

    # then
    content = get_graphql_content(response)
    data = content["data"]["pages"]["edges"]
    assert len(data) == page_count


def test_query_pages_by_app(app_api_client, page_list, page, permission_manage_pages):
    # given
    unpublished_page = page
    unpublished_page.is_published = False
    unpublished_page.save(update_fields=["is_published"])

    page_count = Page.objects.count()

    app_api_client.app.permissions.add(permission_manage_pages)

    # when
    response = app_api_client.post_graphql(PAGES_QUERY)

    # then
    content = get_graphql_content(response)
    data = content["data"]["pages"]["edges"]
    assert len(data) == page_count


def test_query_pages_by_staff_no_perm(staff_api_client, page_list, page):
    # given
    unpublished_page = page
    unpublished_page.is_published = False
    unpublished_page.save(update_fields=["is_published"])

    page_count = Page.objects.count()

    # when
    response = staff_api_client.post_graphql(PAGES_QUERY)

    # then
    content = get_graphql_content(response)
    data = content["data"]["pages"]["edges"]
    assert len(data) == page_count - 1


def test_query_pages_by_app_no_perm(app_api_client, page_list, page):
    """Ensure app without manage pages permission can query only published pages."""
    # given
    unpublished_page = page
    unpublished_page.is_published = False
    unpublished_page.save(update_fields=["is_published"])

    page_count = Page.objects.count()

    # when
    response = app_api_client.post_graphql(PAGES_QUERY)

    # then
    content = get_graphql_content(response)
    data = content["data"]["pages"]["edges"]
    assert len(data) == page_count - 1


def test_query_pages_by_customer(api_client, page_list, page):
    """Ensure customer user can query only published pages."""
    # given
    unpublished_page = page
    unpublished_page.is_published = False
    unpublished_page.save(update_fields=["is_published"])

    page_count = Page.objects.count()

    # when
    response = api_client.post_graphql(PAGES_QUERY)

    # then
    content = get_graphql_content(response)
    data = content["data"]["pages"]["edges"]
    assert len(data) == page_count - 1


PAGES_QUERY_WITH_ATTRIBUTE_AND_CHANNEL = """
    query ($channel: String) {
        pages(first: 10, channel: $channel) {
            edges {
                node {
                    id
                    title
                    slug
                    pageType {
                        id
                    }
                    content
                    contentJson
                    attributes {
                        attribute {
                            slug
                        }
                        values {
                            id
                            slug
                            reference
                            referencedObject {
                                __typename
                                ... on Page {
                                    id
                                }
                                ... on ProductVariant {
                                    id
                                    pricing {
                                    onSale
                                    }
                                }
                                ... on Product {
                                    id
                                    created
                                    pricing {
                                    onSale
                                    }
                                }
                                }
                        }
                    }
                }
            }
        }
    }
"""


def test_pages_attribute_with_referenced_product_variant_object_and_channel_slug(
    staff_api_client,
    page_type_variant_reference_attribute,
    permission_manage_pages,
    page,
    product,
    channel_USD,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_pages)

    product_variant = product.variants.first()
    page_type = page.page_type
    page_type.page_attributes.all().delete()
    page_type.page_attributes.add(page_type_variant_reference_attribute)

    attribute_value = AttributeValue.objects.create(
        attribute=page_type_variant_reference_attribute,
        name=f"Variant {product_variant.pk}",
        slug=f"variant-{product_variant.pk}",
        reference_variant=product_variant,
    )

    associate_attribute_values_to_instance(
        page,
        {page_type_variant_reference_attribute.pk: [attribute_value]},
    )

    query = PAGES_QUERY_WITH_ATTRIBUTE_AND_CHANNEL

    # when
    variables = {
        "channel": channel_USD.slug,
    }
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    pages_data = content["data"]["pages"]["edges"]
    assert len(pages_data) == 1
    page_data = pages_data[0]["node"]
    page_attributes = page_data["attributes"]
    assert len(page_attributes) == 1

    attribute_with_reference = page_attributes[0]
    assert attribute_with_reference["attribute"]["slug"] == "variant-reference"

    assert len(attribute_with_reference["values"]) == 1
    value = attribute_with_reference["values"][0]
    assert value["reference"] == graphene.Node.to_global_id(
        "ProductVariant", product_variant.id
    )
    assert value["referencedObject"]["__typename"] == "ProductVariant"
    # having pricing object means that we passed channel_slug to the variant
    assert value["referencedObject"]["pricing"]


def test_pages_attribute_with_referenced_product_object_and_channel_slug(
    staff_api_client,
    page_type_product_reference_attribute,
    permission_manage_pages,
    page,
    product,
    channel_USD,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_pages)

    page_type = page.page_type
    page_type.page_attributes.all().delete()
    page_type.page_attributes.add(page_type_product_reference_attribute)

    attribute_value = AttributeValue.objects.create(
        attribute=page_type_product_reference_attribute,
        name=f"Product {product.pk}",
        slug=f"product-{product.pk}",
        reference_product=product,
    )

    associate_attribute_values_to_instance(
        page,
        {page_type_product_reference_attribute.pk: [attribute_value]},
    )

    query = PAGES_QUERY_WITH_ATTRIBUTE_AND_CHANNEL

    # when
    variables = {
        "channel": channel_USD.slug,
    }
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    pages_data = content["data"]["pages"]["edges"]
    assert len(pages_data) == 1
    page_data = pages_data[0]["node"]
    page_attributes = page_data["attributes"]
    assert len(page_attributes) == 1

    attribute_with_reference = page_attributes[0]
    assert attribute_with_reference["attribute"]["slug"] == "product-reference"

    assert len(attribute_with_reference["values"]) == 1
    value = attribute_with_reference["values"][0]
    assert value["reference"] == graphene.Node.to_global_id("Product", product.id)
    assert value["referencedObject"]["__typename"] == "Product"
    # having pricing object means that we passed channel_slug to the product
    assert value["referencedObject"]["pricing"]


def test_pages_attribute_with_incorrect_channel_slug(
    staff_api_client,
    page_type_variant_reference_attribute,
    permission_manage_pages,
    page,
    product,
    channel_USD,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_pages)

    query = PAGES_QUERY_WITH_ATTRIBUTE_AND_CHANNEL

    # when
    variables = {
        "channel": "non-existing-channel-slug",
    }
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    pages_data = content["data"]["pages"]["edges"]
    assert len(pages_data) == 0
