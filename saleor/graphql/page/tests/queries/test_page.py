import graphene

from .....attribute.models import AttributeValue
from .....attribute.utils import associate_attribute_values_to_instance
from .....tests.utils import dummy_editorjs
from ....tests.utils import get_graphql_content, get_graphql_content_from_response

PAGE_QUERY = """
    query PageQuery($id: ID, $slug: String) {
        page(id: $id, slug: $slug) {
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
    assert (
        page_data["content"]
        == page_data["contentJson"]
        == dummy_editorjs("Test content.", True)
    )
    assert page_data["title"] == page.title
    assert page_data["slug"] == page.slug
    assert page_data["pageType"]["id"] == graphene.Node.to_global_id(
        "PageType", page.page_type.pk
    )

    expected_attributes = []
    for attr in page_type.page_attributes.all():
        values = (
            [
                {
                    "slug": page_attr_value.slug,
                    "id": graphene.Node.to_global_id(
                        "AttributeValue", page_attr_value.pk
                    ),
                }
            ]
            if attr.slug == page_attr.slug
            else []
        )
        expected_attributes.append({"attribute": {"slug": attr.slug}, "values": values})

    for attr_data in page_data["attributes"]:
        assert attr_data in expected_attributes

    # query by slug
    variables = {"slug": page.slug}
    response = user_api_client.post_graphql(PAGE_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["page"]["id"] == graphene.Node.to_global_id("Page", page.id)


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


def test_staff_query_unpublished_page_by_id(
    staff_api_client, page, permission_manage_pages
):
    page.is_published = False
    page.save()

    # query by ID
    variables = {"id": graphene.Node.to_global_id("Page", page.id)}
    response = staff_api_client.post_graphql(
        PAGE_QUERY,
        variables,
        permissions=[permission_manage_pages],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    assert content["data"]["page"]["id"] == variables["id"]


def test_staff_query_unpublished_page_by_id_without_required_permission(
    staff_api_client,
    page,
):
    page.is_published = False
    page.save()

    # query by ID
    variables = {"id": graphene.Node.to_global_id("Page", page.id)}
    response = staff_api_client.post_graphql(PAGE_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["page"] is None


def test_app_query_unpublished_page_by_id(
    app_api_client, page, permission_manage_pages
):
    # given
    page.is_published = False
    page.save()

    app_api_client.app.permissions.add(permission_manage_pages)

    variables = {"id": graphene.Node.to_global_id("Page", page.id)}

    # when
    response = app_api_client.post_graphql(
        PAGE_QUERY,
        variables,
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["page"]["id"] == variables["id"]


def test_app_query_unpublished_page_by_id_without_required_permission(
    app_api_client,
    page,
):
    # given
    page.is_published = False
    page.save()

    variables = {"id": graphene.Node.to_global_id("Page", page.id)}

    # when
    response = app_api_client.post_graphql(PAGE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["page"] is None


def test_app_query_unpublished_page_by_slug(
    app_api_client, page, permission_manage_pages
):
    # given
    page.is_published = False
    page.save()

    app_api_client.app.permissions.add(permission_manage_pages)

    variables = {"slug": page.slug}

    # when
    response = app_api_client.post_graphql(
        PAGE_QUERY,
        variables,
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["page"]["id"] == graphene.Node.to_global_id("Page", page.id)


def test_app_query_unpublished_page_by_slug_without_required_permission(
    app_api_client,
    page,
):
    # given
    page.is_published = False
    page.save()

    # when
    variables = {"slug": page.slug}

    # then
    response = app_api_client.post_graphql(PAGE_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["page"] is None


def test_staff_query_unpublished_page_by_slug(
    staff_api_client, page, permission_manage_pages
):
    page.is_published = False
    page.save()

    # query by slug
    variables = {"slug": page.slug}
    response = staff_api_client.post_graphql(
        PAGE_QUERY,
        variables,
        permissions=[permission_manage_pages],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    assert content["data"]["page"]["id"] == graphene.Node.to_global_id("Page", page.id)


def test_staff_query_unpublished_page_by_slug_without_required_permission(
    staff_api_client,
    page,
):
    page.is_published = False
    page.save()

    # query by slug
    variables = {"slug": page.slug}
    response = staff_api_client.post_graphql(PAGE_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["page"] is None


def test_staff_query_page_by_invalid_id(staff_api_client, page):
    id = "bh/"
    variables = {"id": id}
    response = staff_api_client.post_graphql(PAGE_QUERY, variables)
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == f"Couldn't resolve id: {id}."
    assert content["data"]["page"] is None


def test_staff_query_page_with_invalid_object_type(staff_api_client, page):
    variables = {"id": graphene.Node.to_global_id("Order", page.id)}
    response = staff_api_client.post_graphql(PAGE_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["page"] is None


def test_get_page_with_sorted_attribute_values(
    staff_api_client,
    page,
    product_list,
    page_type_product_reference_attribute,
    permission_manage_pages,
):
    # given
    page_type = page.page_type
    page_type.page_attributes.set([page_type_product_reference_attribute])

    attr_value_1 = AttributeValue.objects.create(
        attribute=page_type_product_reference_attribute,
        name=product_list[0].name,
        slug=f"{page.pk}_{product_list[0].pk}",
    )
    attr_value_2 = AttributeValue.objects.create(
        attribute=page_type_product_reference_attribute,
        name=product_list[1].name,
        slug=f"{page.pk}_{product_list[1].pk}",
    )
    attr_value_3 = AttributeValue.objects.create(
        attribute=page_type_product_reference_attribute,
        name=product_list[2].name,
        slug=f"{page.pk}_{product_list[2].pk}",
    )

    attr_values = [attr_value_2, attr_value_1, attr_value_3]
    associate_attribute_values_to_instance(
        page, page_type_product_reference_attribute, *attr_values
    )

    page_id = graphene.Node.to_global_id("Page", page.id)
    variables = {"id": page_id}
    staff_api_client.user.user_permissions.add(permission_manage_pages)

    # when
    response = staff_api_client.post_graphql(PAGE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["page"]
    assert len(data["attributes"]) == 1
    values = data["attributes"][0]["values"]
    assert len(values) == 3
    assert [value["id"] for value in values] == [
        graphene.Node.to_global_id("AttributeValue", val.pk) for val in attr_values
    ]
