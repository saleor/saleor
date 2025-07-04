import graphene
import pytest

from .....attribute.models import AttributeValue
from .....attribute.tests.model_helpers import (
    get_page_attribute_values,
    get_page_attributes,
)
from .....attribute.utils import associate_attribute_values_to_instance
from .....page.models import Page, PageTranslation
from .....tests.utils import dummy_editorjs
from ....core.enums import LanguageCodeEnum
from ....tests.utils import get_graphql_content, get_graphql_content_from_response

PAGE_QUERY = """
    query PageQuery($id: ID, $slug: String, $slugLanguageCode: LanguageCodeEnum) {
        page(id: $id, slug: $slug, slugLanguageCode: $slugLanguageCode) {
            id
            title
            slug
            created
            pageType {
                id
            }
            content
            contentJson
            attributes {
                attribute {
                    id
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

    page_attr = get_page_attributes(page).first()
    assert page_attr is not None
    assert get_page_attribute_values(page, page_attr).count() == 1

    page_attr_value = page_attr.values.first()

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
        attr_id = graphene.Node.to_global_id("Attribute", attr.pk)
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
        expected_attributes.append(
            {"attribute": {"id": attr_id, "slug": attr.slug}, "values": values}
        )

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
    assert content["errors"][0]["message"] == f"Invalid ID: {id}. Expected: Page."
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
        page, {page_type_product_reference_attribute.pk: attr_values}
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


def test_page_attributes_not_visible_in_storefront_for_customer_is_not_returned(
    user_api_client, page
):
    # given
    attribute = page.page_type.page_attributes.first()
    attribute.visible_in_storefront = False
    attribute.save(update_fields=["visible_in_storefront"])
    visible_attrs_count = page.page_type.page_attributes.filter(
        visible_in_storefront=True
    ).count()

    # when
    variables = {
        "id": graphene.Node.to_global_id("Page", page.pk),
    }
    response = user_api_client.post_graphql(
        PAGE_QUERY,
        variables,
    )

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["page"]["attributes"]) == visible_attrs_count
    attr_data = {}
    for attr in content["data"]["page"]["attributes"]:
        if attr["attribute"]["id"] == graphene.Node.to_global_id(
            "Attribute", attribute.pk
        ):
            attr_data = attr
            attr_data.pop("values", None)
            break

    assert attr_data == {}


def test_page_attributes_visible_in_storefront_for_customer_is_returned(
    user_api_client, page
):
    # given
    attribute = page.page_type.page_attributes.first()
    attribute.visible_in_storefront = True
    attribute.save(update_fields=["visible_in_storefront"])

    # when
    variables = {
        "id": graphene.Node.to_global_id("Page", page.pk),
    }
    response = user_api_client.post_graphql(
        PAGE_QUERY,
        variables,
    )

    # then
    content = get_graphql_content(response)
    attr_data = {}
    for attr in content["data"]["page"]["attributes"]:
        if attr["attribute"]["id"] == graphene.Node.to_global_id(
            "Attribute", attribute.pk
        ):
            attr_data = attr
            attr_data.pop("values", None)
            break

    assert attr_data == {
        "attribute": {
            "id": graphene.Node.to_global_id("Attribute", attribute.pk),
            "slug": attribute.slug,
        }
    }


@pytest.mark.parametrize("visible_in_storefront", [False, True])
def test_page_attributes_visible_in_storefront_for_staff_is_always_returned(
    visible_in_storefront,
    staff_api_client,
    page,
    permission_manage_pages,
):
    # given
    attribute = page.page_type.page_attributes.first()
    attribute.visible_in_storefront = visible_in_storefront
    attribute.save(update_fields=["visible_in_storefront"])

    # when
    variables = {
        "id": graphene.Node.to_global_id("Page", page.pk),
    }
    staff_api_client.user.user_permissions.add(permission_manage_pages)
    response = staff_api_client.post_graphql(
        PAGE_QUERY,
        variables,
    )

    # then
    content = get_graphql_content(response)
    attr_data = {}
    for attr in content["data"]["page"]["attributes"]:
        if attr["attribute"]["id"] == graphene.Node.to_global_id(
            "Attribute", attribute.pk
        ):
            attr_data = attr
            attr_data.pop("values", None)
            break

    assert attr_data == {
        "attribute": {
            "id": graphene.Node.to_global_id("Attribute", attribute.pk),
            "slug": attribute.slug,
        }
    }


def test_page_query_by_translated_slug(user_api_client, page, page_translation_fr):
    # given
    slug = "french-article"
    PageTranslation.objects.filter(
        page=page, language_code=page_translation_fr.language_code
    ).update(slug=slug)

    # when
    variables = {"slug": slug, "slugLanguageCode": LanguageCodeEnum.FR.name}
    response = user_api_client.post_graphql(
        PAGE_QUERY,
        variables,
    )

    # then
    content = get_graphql_content(response)
    page_data = content["data"]["page"]

    assert page_data is not None
    assert page_data["title"] == page.title


QUERY_PAGE_WITH_ATTRIBUTE = """
query Page($id: ID!, $slug: String!) {
    page(id: $id) {
        attribute(slug: $slug) {
            attribute {
                id
                slug
            }
        }
        attributes {
            attribute {
                id
                slug
            }
            values {
                reference
                referencedObject {
                    __typename
                    ... on Page {
                        id
                        publicationDate
                    }
                    ... on ProductVariant {
                        id
                        created
                    }
                    ... on Product {
                        id
                        created
                    }
                }
            }
        }
    }
}
"""


def test_page_attribute_field_filtering(staff_api_client, page):
    # given
    slug = page.page_type.page_attributes.first().slug

    variables = {
        "id": graphene.Node.to_global_id("Page", page.pk),
        "slug": slug,
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGE_WITH_ATTRIBUTE,
        variables,
    )

    # then
    expected_slug = slug
    content = get_graphql_content(response)
    queried_slug = content["data"]["page"]["attribute"]["attribute"]["slug"]
    assert queried_slug == expected_slug


def test_page_attribute_field_filtering_not_found(staff_api_client, page):
    # given
    slug = ""

    variables = {
        "id": graphene.Node.to_global_id("Page", page.pk),
        "slug": slug,
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGE_WITH_ATTRIBUTE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["page"]["attribute"] is None


def test_page_attribute_not_visible_in_storefront_for_customer_is_not_returned(
    user_api_client, page
):
    # given
    attribute = page.page_type.page_attributes.first()
    attribute.visible_in_storefront = False
    attribute.save(update_fields=["visible_in_storefront"])
    visible_attrs_count = page.page_type.page_attributes.filter(
        visible_in_storefront=True
    ).count()

    # when
    variables = {
        "id": graphene.Node.to_global_id("Page", page.pk),
        "slug": attribute.slug,
    }
    response = user_api_client.post_graphql(
        QUERY_PAGE_WITH_ATTRIBUTE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["page"]["attribute"] is None
    assert len(content["data"]["page"]["attributes"]) == visible_attrs_count
    attr_data = {
        "attribute": {
            "id": graphene.Node.to_global_id("Attribute", attribute.pk),
            "slug": attribute.slug,
        }
    }
    assert attr_data not in content["data"]["page"]["attributes"]


def test_page_attribute_visible_in_storefront_for_customer_is_returned(
    user_api_client, page
):
    # given
    attribute = page.page_type.page_attributes.first()
    attribute.visible_in_storefront = True
    attribute.save(update_fields=["visible_in_storefront"])

    # when
    variables = {
        "id": graphene.Node.to_global_id("Page", page.pk),
        "slug": attribute.slug,
    }
    response = user_api_client.post_graphql(
        QUERY_PAGE_WITH_ATTRIBUTE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["page"]["attribute"]["attribute"]["slug"] == attribute.slug


@pytest.mark.parametrize("visible_in_storefront", [False, True])
def test_page_attribute_visible_in_storefront_for_staff_is_always_returned(
    visible_in_storefront,
    staff_api_client,
    page,
    permission_manage_pages,
):
    # given
    attribute = page.page_type.page_attributes.first()
    attribute.visible_in_storefront = visible_in_storefront
    attribute.save(update_fields=["visible_in_storefront"])

    # when
    variables = {
        "id": graphene.Node.to_global_id("Page", page.pk),
        "slug": attribute.slug,
    }
    staff_api_client.user.user_permissions.add(permission_manage_pages)
    response = staff_api_client.post_graphql(
        QUERY_PAGE_WITH_ATTRIBUTE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["page"]["attribute"]["attribute"]["slug"] == attribute.slug


def test_page_attribute_with_referenced_page_object(
    staff_api_client,
    page_type_page_reference_attribute,
    permission_manage_pages,
    page,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_pages)

    # Create a second page to reference
    referenced_page = Page.objects.create(
        title="Referenced Page",
        slug="referenced-page",
        page_type=page.page_type,
        is_published=True,
    )

    page_type = page.page_type
    page_type.page_attributes.all().delete()
    page_type.page_attributes.add(page_type_page_reference_attribute)

    attribute_value = AttributeValue.objects.create(
        attribute=page_type_page_reference_attribute,
        name=f"Page {referenced_page.pk}",
        slug=f"page-{referenced_page.pk}",
        reference_page=referenced_page,
    )

    associate_attribute_values_to_instance(
        page, {page_type_page_reference_attribute.pk: [attribute_value]}
    )

    query = QUERY_PAGE_WITH_ATTRIBUTE

    # when
    variables = {
        "id": graphene.Node.to_global_id("Page", page.pk),
        "slug": page_type_page_reference_attribute.slug,
    }
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    page_data = content["data"]["page"]
    page_attributes = page_data["attributes"]
    assert len(page_attributes) == 1

    attribute_with_reference = page_attributes[0]
    assert attribute_with_reference["attribute"]["slug"] == "page-reference"

    assert len(attribute_with_reference["values"]) == 1
    value = attribute_with_reference["values"][0]
    assert value["reference"] == graphene.Node.to_global_id("Page", referenced_page.id)
    assert value["referencedObject"]["__typename"] == "Page"
    assert value["referencedObject"]["id"] == graphene.Node.to_global_id(
        "Page", referenced_page.id
    )


def test_page_attribute_with_referenced_product_variant_object(
    staff_api_client,
    page_type_variant_reference_attribute,
    permission_manage_pages,
    page,
    product,
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

    query = QUERY_PAGE_WITH_ATTRIBUTE

    # when
    variables = {
        "id": graphene.Node.to_global_id("Page", page.pk),
        "slug": page_type_variant_reference_attribute.slug,
    }
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    page_data = content["data"]["page"]
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
    assert value["referencedObject"]["id"] == graphene.Node.to_global_id(
        "ProductVariant", product_variant.id
    )


def test_page_attribute_with_referenced_product_object(
    staff_api_client,
    page_type_product_reference_attribute,
    permission_manage_pages,
    page,
    product,
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

    query = QUERY_PAGE_WITH_ATTRIBUTE

    # when
    variables = {
        "id": graphene.Node.to_global_id("Page", page.pk),
        "slug": page_type_product_reference_attribute.slug,
    }
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    page_data = content["data"]["page"]
    page_attributes = page_data["attributes"]
    assert len(page_attributes) == 1

    attribute_with_reference = page_attributes[0]
    assert attribute_with_reference["attribute"]["slug"] == "product-reference"

    assert len(attribute_with_reference["values"]) == 1
    value = attribute_with_reference["values"][0]
    assert value["reference"] == graphene.Node.to_global_id("Product", product.id)
    assert value["referencedObject"]["__typename"] == "Product"
    assert value["referencedObject"]["id"] == graphene.Node.to_global_id(
        "Product", product.id
    )


QUERY_PAGE_WITH_ATTRIBUTE_AND_CHANNEL = """
query Page($id: ID!, $channel: String) {
  page(id: $id, channel: $channel) {
    attributes {
      attribute {
        id
        slug
      }
      values {
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
"""


def test_page_attribute_with_referenced_page_object_and_channel_slug(
    staff_api_client,
    page_type_page_reference_attribute,
    permission_manage_pages,
    page,
    channel_USD,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_pages)

    # Create a second page to reference
    referenced_page = Page.objects.create(
        title="Referenced Page",
        slug="referenced-page",
        page_type=page.page_type,
        is_published=True,
    )

    page_type = page.page_type
    page_type.page_attributes.all().delete()
    page_type.page_attributes.add(page_type_page_reference_attribute)

    attribute_value = AttributeValue.objects.create(
        attribute=page_type_page_reference_attribute,
        name=f"Page {referenced_page.pk}",
        slug=f"page-{referenced_page.pk}",
        reference_page=referenced_page,
    )

    associate_attribute_values_to_instance(
        page, {page_type_page_reference_attribute.pk: [attribute_value]}
    )

    query = QUERY_PAGE_WITH_ATTRIBUTE_AND_CHANNEL

    # when
    variables = {
        "id": graphene.Node.to_global_id("Page", page.pk),
        "channel": channel_USD.slug,
    }
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    page_data = content["data"]["page"]
    page_attributes = page_data["attributes"]
    assert len(page_attributes) == 1

    attribute_with_reference = page_attributes[0]
    assert attribute_with_reference["attribute"]["slug"] == "page-reference"

    assert len(attribute_with_reference["values"]) == 1
    value = attribute_with_reference["values"][0]
    assert value["reference"] == graphene.Node.to_global_id("Page", referenced_page.id)
    assert value["referencedObject"]["__typename"] == "Page"
    assert value["referencedObject"]["id"] == graphene.Node.to_global_id(
        "Page", referenced_page.id
    )


def test_page_attribute_with_referenced_product_variant_object_and_channel_slug(
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

    query = QUERY_PAGE_WITH_ATTRIBUTE_AND_CHANNEL

    # when
    variables = {
        "id": graphene.Node.to_global_id("Page", page.pk),
        "channel": channel_USD.slug,
    }
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    page_data = content["data"]["page"]
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


def test_page_attribute_with_referenced_product_object_and_channel_slug(
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

    query = QUERY_PAGE_WITH_ATTRIBUTE_AND_CHANNEL

    # when
    variables = {
        "id": graphene.Node.to_global_id("Page", page.pk),
        "channel": channel_USD.slug,
    }
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    page_data = content["data"]["page"]
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


def test_page_channel_not_found(staff_api_client, page, permission_manage_pages):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_pages)

    variables = {
        "id": graphene.Node.to_global_id("Page", page.pk),
        "channel": "not-existing-channel",
    }
    query = """
    query Page($id: ID!, $channel: String) {
        page(id: $id, channel: $channel) {
            id
        }
    }
    """

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["page"] is None
