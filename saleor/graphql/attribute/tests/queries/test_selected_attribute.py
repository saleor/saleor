from datetime import UTC, datetime

import graphene

from .....attribute import AttributeEntityType, AttributeInputType, AttributeType
from .....attribute.models.base import AttributeValue, AttributeValueTranslation
from .....attribute.utils import associate_attribute_values_to_instance
from ....tests.utils import get_graphql_content
from ...types import (
    ASSIGNED_ATTRIBUTE_MAP,
    ASSIGNED_MULTI_REFERENCE_MAP,
    ASSIGNED_SINGLE_REFERENCE_MAP,
)

PAGE_QUERY = """
    query PageQuery($id: ID) {
        page(id: $id) {
            attributes {
                values {
                    id
                    name
                }
            }
        }
    }
"""


def test_attribute_value_name_when_referenced_product_was_changed(
    staff_api_client,
    product,
    page,
    page_type_product_reference_attribute,
):
    # given
    page_type = page.page_type
    page_type.page_attributes.set([page_type_product_reference_attribute])

    attr_value = AttributeValue.objects.create(
        attribute=page_type_product_reference_attribute,
        name=product.name,
        slug=f"{page.pk}_{product.pk}",
        reference_product_id=product.pk,
    )
    associate_attribute_values_to_instance(
        page, {page_type_product_reference_attribute.pk: [attr_value]}
    )

    new_product_name = "New Product Name"
    product.name = new_product_name
    product.save(update_fields=["name"])

    # when
    response = staff_api_client.post_graphql(
        PAGE_QUERY,
        variables={"id": graphene.Node.to_global_id("Page", page.pk)},
    )

    # then
    content = get_graphql_content(response)

    assert len(content["data"]["page"]["attributes"]) == 1
    assert len(content["data"]["page"]["attributes"][0]["values"]) == 1
    data = content["data"]["page"]["attributes"][0]["values"][0]
    assert data["name"] == new_product_name


def test_attribute_value_name_when_referenced_variant_was_changed(
    staff_api_client,
    variant,
    page,
    page_type_variant_reference_attribute,
):
    # given
    page_type = page.page_type
    page_type.page_attributes.set([page_type_variant_reference_attribute])

    attr_value = AttributeValue.objects.create(
        attribute=page_type_variant_reference_attribute,
        name=variant.name,
        slug=f"{page.pk}_{variant.pk}",
        reference_variant_id=variant.pk,
    )
    associate_attribute_values_to_instance(
        page, {page_type_variant_reference_attribute.pk: [attr_value]}
    )
    product_name = "Product Name"
    variant.product.name = product_name
    variant.product.save(update_fields=["name"])

    new_variant_name = "New Variant Name"
    variant.name = new_variant_name
    variant.save(update_fields=["name"])

    # when
    response = staff_api_client.post_graphql(
        PAGE_QUERY,
        variables={"id": graphene.Node.to_global_id("Page", page.pk)},
    )

    # then
    content = get_graphql_content(response)

    assert len(content["data"]["page"]["attributes"]) == 1
    assert len(content["data"]["page"]["attributes"][0]["values"]) == 1
    data = content["data"]["page"]["attributes"][0]["values"][0]
    assert data["name"] == f"{product_name}: {new_variant_name}"


def test_attribute_value_name_when_referenced_page_was_changed(
    staff_api_client,
    page,
    page_list,
    page_type_page_reference_attribute,
):
    # given
    referenced_page = page_list[0]

    page_type = page.page_type
    page_type.page_attributes.set([page_type_page_reference_attribute])

    attr_value = AttributeValue.objects.create(
        attribute=page_type_page_reference_attribute,
        name=referenced_page.title,
        slug=f"{page.pk}_{referenced_page.pk}",
        reference_page_id=referenced_page.pk,
    )
    associate_attribute_values_to_instance(
        page, {page_type_page_reference_attribute.pk: [attr_value]}
    )

    new_page_title = "New Page Title"
    referenced_page.title = new_page_title
    referenced_page.save(update_fields=["title"])

    # when
    response = staff_api_client.post_graphql(
        PAGE_QUERY,
        variables={"id": graphene.Node.to_global_id("Page", page.pk)},
    )

    # then
    content = get_graphql_content(response)

    assert len(content["data"]["page"]["attributes"]) == 1
    assert len(content["data"]["page"]["attributes"][0]["values"]) == 1
    data = content["data"]["page"]["attributes"][0]["values"][0]
    assert data["name"] == new_page_title


ASSIGNED_NUMERIC_ATTRIBUTE_QUERY = """
query PageQuery($id: ID) {
  page(id: $id) {
    assignedAttributes(limit:10) {
      ... on AssignedNumericAttribute {
        attribute {
          id
        }
        value
      }
    }
  }
}
"""


def test_assigned_numeric_attribute(staff_api_client, page, numeric_attribute):
    # given
    page_type = page.page_type
    page_type.page_attributes.set([numeric_attribute])

    attr_value = numeric_attribute.values.first()

    associate_attribute_values_to_instance(page, {numeric_attribute.pk: [attr_value]})

    # when
    response = staff_api_client.post_graphql(
        ASSIGNED_NUMERIC_ATTRIBUTE_QUERY,
        variables={"id": graphene.Node.to_global_id("Page", page.pk)},
    )

    # then
    content = get_graphql_content(response)

    assert len(content["data"]["page"]["assignedAttributes"]) == 1
    assert (
        content["data"]["page"]["assignedAttributes"][0]["value"] == attr_value.numeric
    )


ASSIGNED_TEXT_ATTRIBUTE_QUERY = """
query PageQuery($id: ID) {
  page(id: $id) {
    assignedAttributes(limit:10) {
      ...on AssignedTextAttribute{
        value
        translation(languageCode:FR)
      }
    }
  }
}
"""


def test_assigned_text_attribute_translation(
    staff_api_client,
    page,
    rich_text_attribute_page_type,
    translated_page_unique_attribute_value,
):
    # given
    page_type = page.page_type
    page_type.page_attributes.set([rich_text_attribute_page_type])

    attr_value = rich_text_attribute_page_type.values.first()
    assert attr_value.id == translated_page_unique_attribute_value.attribute_value_id

    associate_attribute_values_to_instance(
        page, {rich_text_attribute_page_type.pk: [attr_value]}
    )

    assert attr_value.rich_text is not None

    # when
    response = staff_api_client.post_graphql(
        ASSIGNED_TEXT_ATTRIBUTE_QUERY,
        variables={"id": graphene.Node.to_global_id("Page", page.pk)},
    )

    # then
    content = get_graphql_content(response)

    assert len(content["data"]["page"]["assignedAttributes"]) == 1
    assert (
        content["data"]["page"]["assignedAttributes"][0]["translation"]
        == translated_page_unique_attribute_value.rich_text
    )


def test_assigned_text_attribute(staff_api_client, page, rich_text_attribute):
    # given
    page_type = page.page_type
    page_type.page_attributes.set([rich_text_attribute])

    attr_value = rich_text_attribute.values.first()

    associate_attribute_values_to_instance(page, {rich_text_attribute.pk: [attr_value]})

    assert attr_value.rich_text is not None

    # when
    response = staff_api_client.post_graphql(
        ASSIGNED_TEXT_ATTRIBUTE_QUERY,
        variables={"id": graphene.Node.to_global_id("Page", page.pk)},
    )

    # then
    content = get_graphql_content(response)

    assert len(content["data"]["page"]["assignedAttributes"]) == 1
    assert (
        content["data"]["page"]["assignedAttributes"][0]["value"]
        == attr_value.rich_text
    )


ASSIGNED_PLAIN_TEXT_ATTRIBUTE_QUERY = """
query PageQuery($id: ID) {
  page(id: $id) {
    assignedAttributes(limit:10) {
      ...on AssignedPlainTextAttribute{
        value
        translation(languageCode:FR)
      }
    }
  }
}
"""


def test_assigned_plain_text_attribute_translation(
    staff_api_client,
    page,
    plain_text_attribute_page_type,
    translated_page_unique_attribute_value,
):
    # given
    page_type = page.page_type
    page_type.page_attributes.set([plain_text_attribute_page_type])

    attr_value = plain_text_attribute_page_type.values.first()
    translation = AttributeValueTranslation.objects.create(
        language_code="fr",
        attribute_value=attr_value,
        plain_text="French description.",
    )

    assert attr_value.id == translation.attribute_value_id

    associate_attribute_values_to_instance(
        page, {plain_text_attribute_page_type.pk: [attr_value]}
    )

    assert attr_value.plain_text is not None

    # when
    response = staff_api_client.post_graphql(
        ASSIGNED_PLAIN_TEXT_ATTRIBUTE_QUERY,
        variables={"id": graphene.Node.to_global_id("Page", page.pk)},
    )

    # then
    content = get_graphql_content(response)

    assert len(content["data"]["page"]["assignedAttributes"]) == 1
    assert (
        content["data"]["page"]["assignedAttributes"][0]["translation"]
        == translation.plain_text
    )


def test_assigned_plain_text_attribute(staff_api_client, page, plain_text_attribute):
    # given
    page_type = page.page_type
    page_type.page_attributes.set([plain_text_attribute])

    attr_value = plain_text_attribute.values.first()

    associate_attribute_values_to_instance(
        page, {plain_text_attribute.pk: [attr_value]}
    )

    assert attr_value.plain_text is not None

    # when
    response = staff_api_client.post_graphql(
        ASSIGNED_PLAIN_TEXT_ATTRIBUTE_QUERY,
        variables={"id": graphene.Node.to_global_id("Page", page.pk)},
    )

    # then
    content = get_graphql_content(response)

    assert len(content["data"]["page"]["assignedAttributes"]) == 1
    assert (
        content["data"]["page"]["assignedAttributes"][0]["value"]
        == attr_value.plain_text
    )


ASSIGNED_FILE_ATTRIBUTE_QUERY = """
query PageQuery($id: ID) {
  page(id: $id) {
    assignedAttributes(limit:10) {
      ...on AssignedFileAttribute{
        value {
          url
          contentType
        }
      }
    }
  }
}
"""


def test_assigned_file_attribute(staff_api_client, page, file_attribute):
    # given
    page_type = page.page_type
    page_type.page_attributes.set([file_attribute])

    attr_value = file_attribute.values.first()
    attr_value.file_url = "https://example.com/file.pdf"
    attr_value.save()

    associate_attribute_values_to_instance(page, {file_attribute.pk: [attr_value]})

    assert attr_value.file_url is not None

    # when
    response = staff_api_client.post_graphql(
        ASSIGNED_FILE_ATTRIBUTE_QUERY,
        variables={"id": graphene.Node.to_global_id("Page", page.pk)},
    )

    # then
    content = get_graphql_content(response)

    assert len(content["data"]["page"]["assignedAttributes"]) == 1
    assert (
        content["data"]["page"]["assignedAttributes"][0]["value"]["url"]
        == attr_value.file_url
    )
    assert (
        content["data"]["page"]["assignedAttributes"][0]["value"]["contentType"]
        == attr_value.content_type
    )


ASSIGNED_SINGLE_PAGE_REFERENCE_ATTRIBUTE_QUERY = """
query PageQuery($id: ID) {
  page(id: $id) {
    assignedAttributes(limit:10) {
      __typename
      ...on AssignedSinglePageReferenceAttribute{
        value{
          __typename
          slug
        }
      }
    }
  }
}
"""


def test_assigned_single_page_reference_attribute(
    staff_api_client,
    page,
    page_list,
    page_type_page_reference_attribute,
):
    # given
    referenced_page = page_list[0]
    expected_reference_slug = "referenced-page-slug"
    referenced_page.slug = expected_reference_slug
    referenced_page.save(update_fields=["slug"])

    page_type_page_reference_attribute.input_type = AttributeInputType.SINGLE_REFERENCE
    page_type_page_reference_attribute.save()
    page_type = page.page_type
    page_type.page_attributes.set([page_type_page_reference_attribute])

    attr_value = AttributeValue.objects.create(
        attribute=page_type_page_reference_attribute,
        name=referenced_page.title,
        slug=f"{page.pk}_{referenced_page.pk}",
        reference_page_id=referenced_page.pk,
    )
    associate_attribute_values_to_instance(
        page, {page_type_page_reference_attribute.pk: [attr_value]}
    )

    # when
    response = staff_api_client.post_graphql(
        ASSIGNED_SINGLE_PAGE_REFERENCE_ATTRIBUTE_QUERY,
        variables={"id": graphene.Node.to_global_id("Page", page.pk)},
    )

    # then
    content = get_graphql_content(response)

    assert len(content["data"]["page"]["assignedAttributes"]) == 1

    data = content["data"]["page"]["assignedAttributes"][0]["value"]
    assert data["__typename"] == "Page"
    assert data["slug"] == expected_reference_slug


ASSIGNED_SINGLE_PRODUCT_REFERENCE_ATTRIBUTE_QUERY = """
query PageQuery($id: ID) {
  page(id: $id) {
    assignedAttributes(limit:10) {
      __typename
      ...on AssignedSingleProductReferenceAttribute{
        value{
          __typename
          slug
        }
      }
    }
  }
}
"""


def test_assigned_single_product_reference_attribute(
    staff_api_client,
    page,
    product,
    page_type_product_reference_attribute,
):
    # given
    referenced_product = product
    expected_reference_slug = "referenced-product-slug"
    referenced_product.slug = expected_reference_slug
    referenced_product.save(update_fields=["slug"])

    page_type_product_reference_attribute.input_type = (
        AttributeInputType.SINGLE_REFERENCE
    )
    page_type_product_reference_attribute.save()
    page_type = page.page_type
    page_type.page_attributes.set([page_type_product_reference_attribute])

    attr_value = AttributeValue.objects.create(
        attribute=page_type_product_reference_attribute,
        slug=f"{page.pk}_{referenced_product.pk}",
        reference_product_id=referenced_product.pk,
    )
    associate_attribute_values_to_instance(
        page, {page_type_product_reference_attribute.pk: [attr_value]}
    )

    # when
    response = staff_api_client.post_graphql(
        ASSIGNED_SINGLE_PRODUCT_REFERENCE_ATTRIBUTE_QUERY,
        variables={"id": graphene.Node.to_global_id("Page", page.pk)},
    )

    # then
    content = get_graphql_content(response)

    assert len(content["data"]["page"]["assignedAttributes"]) == 1

    data = content["data"]["page"]["assignedAttributes"][0]["value"]
    assert data["__typename"] == "Product"
    assert data["slug"] == expected_reference_slug


ASSIGNED_SINGLE_PRODUCT_VARIANT_REFERENCE_ATTRIBUTE_QUERY = """
query PageQuery($id: ID) {
  page(id: $id) {
    assignedAttributes(limit:10) {
      __typename
      ...on AssignedSingleProductVariantReferenceAttribute{
        value{
          __typename
          sku
        }
      }
    }
  }
}
"""


def test_assigned_single_product_variant_reference_attribute(
    staff_api_client,
    page,
    variant,
    page_type_variant_reference_attribute,
):
    # given
    referenced_variant = variant
    expected_reference_sku = "referenced-variant-sku"
    referenced_variant.sku = expected_reference_sku
    referenced_variant.save(update_fields=["sku"])

    page_type_variant_reference_attribute.input_type = (
        AttributeInputType.SINGLE_REFERENCE
    )
    page_type_variant_reference_attribute.save()
    page_type = page.page_type
    page_type.page_attributes.set([page_type_variant_reference_attribute])

    attr_value = AttributeValue.objects.create(
        attribute=page_type_variant_reference_attribute,
        slug=f"{page.pk}_{referenced_variant.pk}",
        reference_variant_id=referenced_variant.pk,
    )
    associate_attribute_values_to_instance(
        page, {page_type_variant_reference_attribute.pk: [attr_value]}
    )

    # when
    response = staff_api_client.post_graphql(
        ASSIGNED_SINGLE_PRODUCT_VARIANT_REFERENCE_ATTRIBUTE_QUERY,
        variables={"id": graphene.Node.to_global_id("Page", page.pk)},
    )

    # then
    content = get_graphql_content(response)

    assert len(content["data"]["page"]["assignedAttributes"]) == 1

    data = content["data"]["page"]["assignedAttributes"][0]["value"]
    assert data["__typename"] == "ProductVariant"
    assert data["sku"] == expected_reference_sku


ASSIGNED_SINGLE_CATEGORY_REFERENCE_ATTRIBUTE_QUERY = """
query PageQuery($id: ID) {
  page(id: $id) {
    assignedAttributes(limit:10) {
      __typename
      ...on AssignedSingleCategoryReferenceAttribute{
        value{
          __typename
          slug
        }
      }
    }
  }
}
"""


def test_assigned_single_category_reference_attribute(
    staff_api_client,
    page,
    category,
    page_type_category_reference_attribute,
):
    # given
    referenced_category = category
    expected_reference_slug = "referenced-category-slug"
    referenced_category.slug = expected_reference_slug
    referenced_category.save(update_fields=["slug"])

    page_type_category_reference_attribute.input_type = (
        AttributeInputType.SINGLE_REFERENCE
    )
    page_type_category_reference_attribute.save()
    page_type = page.page_type
    page_type.page_attributes.set([page_type_category_reference_attribute])

    attr_value = AttributeValue.objects.create(
        attribute=page_type_category_reference_attribute,
        slug=f"{page.pk}_{referenced_category.pk}",
        reference_category_id=referenced_category.pk,
    )
    associate_attribute_values_to_instance(
        page, {page_type_category_reference_attribute.pk: [attr_value]}
    )

    # when
    response = staff_api_client.post_graphql(
        ASSIGNED_SINGLE_CATEGORY_REFERENCE_ATTRIBUTE_QUERY,
        variables={"id": graphene.Node.to_global_id("Page", page.pk)},
    )

    # then
    content = get_graphql_content(response)

    assert len(content["data"]["page"]["assignedAttributes"]) == 1

    data = content["data"]["page"]["assignedAttributes"][0]["value"]
    assert data["__typename"] == "Category"
    assert data["slug"] == expected_reference_slug


ASSIGNED_SINGLE_COLLECTION_REFERENCE_ATTRIBUTE_QUERY = """
query PageQuery($id: ID) {
  page(id: $id) {
    assignedAttributes(limit:10) {
      __typename
      ...on AssignedSingleCollectionReferenceAttribute{
        value{
          __typename
          slug
        }
      }
    }
  }
}
"""


def test_assigned_single_collection_reference_attribute(
    staff_api_client,
    page,
    collection,
    page_type_collection_reference_attribute,
):
    # given
    referenced_collection = collection
    expected_reference_slug = "referenced-collection-slug"
    referenced_collection.slug = expected_reference_slug
    referenced_collection.save(update_fields=["slug"])

    page_type_collection_reference_attribute.input_type = (
        AttributeInputType.SINGLE_REFERENCE
    )
    page_type_collection_reference_attribute.save()
    page_type = page.page_type
    page_type.page_attributes.set([page_type_collection_reference_attribute])

    attr_value = AttributeValue.objects.create(
        attribute=page_type_collection_reference_attribute,
        slug=f"{page.pk}_{referenced_collection.pk}",
        reference_collection_id=referenced_collection.pk,
    )
    associate_attribute_values_to_instance(
        page, {page_type_collection_reference_attribute.pk: [attr_value]}
    )

    # when
    response = staff_api_client.post_graphql(
        ASSIGNED_SINGLE_COLLECTION_REFERENCE_ATTRIBUTE_QUERY,
        variables={"id": graphene.Node.to_global_id("Page", page.pk)},
    )

    # then
    content = get_graphql_content(response)

    assert len(content["data"]["page"]["assignedAttributes"]) == 1

    data = content["data"]["page"]["assignedAttributes"][0]["value"]
    assert data["__typename"] == "Collection"
    assert data["slug"] == expected_reference_slug


ASSIGNED_MULTIPLE_PAGE_REFERENCE_ATTRIBUTE_QUERY = """
query PageQuery($id: ID) {
  page(id: $id) {
    assignedAttributes(limit:10) {
      ...on AssignedMultiPageReferenceAttribute{
        __typename
        value{
          __typename
          slug
        }
      }
    }
  }
}
"""


def test_assigned_multi_page_reference_attribute(
    staff_api_client,
    page,
    page_list,
    page_type_page_reference_attribute,
):
    # given
    referenced_page = page_list[0]
    expected_reference_slug = "referenced-page-slug"
    referenced_page.slug = expected_reference_slug
    referenced_page.save(update_fields=["slug"])

    page_type_page_reference_attribute.input_type = AttributeInputType.REFERENCE
    page_type_page_reference_attribute.save()
    page_type = page.page_type
    page_type.page_attributes.set([page_type_page_reference_attribute])

    attr_value = AttributeValue.objects.create(
        attribute=page_type_page_reference_attribute,
        name=referenced_page.title,
        slug=f"{page.pk}_{referenced_page.pk}",
        reference_page_id=referenced_page.pk,
    )
    associate_attribute_values_to_instance(
        page, {page_type_page_reference_attribute.pk: [attr_value]}
    )

    # when
    response = staff_api_client.post_graphql(
        ASSIGNED_MULTIPLE_PAGE_REFERENCE_ATTRIBUTE_QUERY,
        variables={"id": graphene.Node.to_global_id("Page", page.pk)},
    )

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["page"]["assignedAttributes"]) == 1

    data = content["data"]["page"]["assignedAttributes"][0]["value"]
    assert len(data) == 1
    single_page_data = data[0]
    assert single_page_data["__typename"] == "Page"
    assert single_page_data["slug"] == expected_reference_slug


ASSIGNED_MULTIPLE_PRODUCT_REFERENCE_ATTRIBUTE_QUERY = """
query PageQuery($id: ID, $valueLimit: PositiveInt) {
  page(id: $id) {
    assignedAttributes(limit:10) {
      ...on AssignedMultiProductReferenceAttribute{
        __typename
        value(limit: $valueLimit) {
          __typename
          slug
        }
      }
    }
  }
}
"""


def test_assigned_multi_product_reference_attribute(
    staff_api_client,
    page,
    product,
    page_type_product_reference_attribute,
):
    # given
    referenced_product = product
    expected_reference_slug = "referenced-product-slug"
    referenced_product.slug = expected_reference_slug
    referenced_product.save(update_fields=["slug"])

    page_type_product_reference_attribute.input_type = AttributeInputType.REFERENCE
    page_type_product_reference_attribute.save()
    page_type = page.page_type
    page_type.page_attributes.set([page_type_product_reference_attribute])

    attr_value = AttributeValue.objects.create(
        attribute=page_type_product_reference_attribute,
        slug=f"{page.pk}_{referenced_product.pk}",
        reference_product_id=referenced_product.pk,
    )

    associate_attribute_values_to_instance(
        page, {page_type_product_reference_attribute.pk: [attr_value]}
    )

    # when
    response = staff_api_client.post_graphql(
        ASSIGNED_MULTIPLE_PRODUCT_REFERENCE_ATTRIBUTE_QUERY,
        variables={"id": graphene.Node.to_global_id("Page", page.pk)},
    )

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["page"]["assignedAttributes"]) == 1

    data = content["data"]["page"]["assignedAttributes"][0]["value"]
    assert len(data) == 1
    single_page_data = data[0]
    assert single_page_data["__typename"] == "Product"
    assert single_page_data["slug"] == expected_reference_slug


def test_applies_limit_to_multi_product_references(
    staff_api_client,
    page,
    product_list,
    page_type_product_reference_attribute,
):
    # given
    page_type = page.page_type

    # make sure that our attribute is on first position
    page_type.page_attributes.update(storefront_search_position=10)
    page_type.page_attributes.set([page_type_product_reference_attribute])
    page_type_product_reference_attribute.input_type = AttributeInputType.REFERENCE
    page_type_product_reference_attribute.storefront_search_position = 1
    page_type_product_reference_attribute.save()

    first_reference = AttributeValue.objects.create(
        attribute=page_type_product_reference_attribute,
        slug=f"{page.pk}_{product_list[0].pk}",
        reference_product_id=product_list[0].pk,
    )
    second_reference = AttributeValue.objects.create(
        attribute=page_type_product_reference_attribute,
        slug=f"{page.pk}_{product_list[1].pk}",
        reference_product_id=product_list[1].pk,
    )

    associate_attribute_values_to_instance(
        page,
        {page_type_product_reference_attribute.pk: [first_reference, second_reference]},
    )
    assert page.attributevalues.count() == 3

    expected_value_limit = 1

    # when
    response = staff_api_client.post_graphql(
        ASSIGNED_MULTIPLE_PRODUCT_REFERENCE_ATTRIBUTE_QUERY,
        variables={
            "id": graphene.Node.to_global_id("Page", page.pk),
            "valueLimit": expected_value_limit,
        },
    )

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["page"]["assignedAttributes"]) == 1
    assert (
        len(content["data"]["page"]["assignedAttributes"][0]["value"])
        == expected_value_limit
    )
    assert (
        content["data"]["page"]["assignedAttributes"][0]["value"][0]["slug"]
        == first_reference.reference_product.slug
    )


ASSIGNED_MULTIPLE_PRODUCT_VARIANT_REFERENCE_ATTRIBUTE_QUERY = """
query PageQuery($id: ID, $valueLimit: PositiveInt) {
  page(id: $id) {
    assignedAttributes(limit:10) {
      ...on AssignedMultiProductVariantReferenceAttribute{
        __typename
        value(limit: $valueLimit) {
          __typename
          sku
        }
      }
    }
  }
}
"""


def test_assigned_multi_product_variant_reference_attribute(
    staff_api_client,
    page,
    variant,
    page_type_variant_reference_attribute,
):
    # given
    referenced_variant = variant
    expected_reference_sku = "referenced-variant-sku"
    referenced_variant.sku = expected_reference_sku
    referenced_variant.save(update_fields=["sku"])

    page_type_variant_reference_attribute.input_type = AttributeInputType.REFERENCE
    page_type_variant_reference_attribute.save()
    page_type = page.page_type
    page_type.page_attributes.set([page_type_variant_reference_attribute])

    attr_value = AttributeValue.objects.create(
        attribute=page_type_variant_reference_attribute,
        slug=f"{page.pk}_{referenced_variant.pk}",
        reference_variant_id=referenced_variant.pk,
    )

    associate_attribute_values_to_instance(
        page, {page_type_variant_reference_attribute.pk: [attr_value]}
    )

    # when
    response = staff_api_client.post_graphql(
        ASSIGNED_MULTIPLE_PRODUCT_VARIANT_REFERENCE_ATTRIBUTE_QUERY,
        variables={"id": graphene.Node.to_global_id("Page", page.pk)},
    )

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["page"]["assignedAttributes"]) == 1

    data = content["data"]["page"]["assignedAttributes"][0]["value"]
    assert len(data) == 1
    single_page_data = data[0]
    assert single_page_data["__typename"] == "ProductVariant"
    assert single_page_data["sku"] == expected_reference_sku


def test_applies_limit_to_multi_variant_references(
    staff_api_client,
    page,
    product_variant_list,
    page_type_variant_reference_attribute,
):
    # given
    page_type = page.page_type

    # make sure that our attribute is on first position
    page_type.page_attributes.update(storefront_search_position=10)
    page_type.page_attributes.set([page_type_variant_reference_attribute])
    page_type_variant_reference_attribute.storefront_search_position = 1
    page_type_variant_reference_attribute.input_type = AttributeInputType.REFERENCE
    page_type_variant_reference_attribute.save()

    first_reference = AttributeValue.objects.create(
        attribute=page_type_variant_reference_attribute,
        slug=f"{page.pk}_{product_variant_list[0].pk}",
        reference_variant_id=product_variant_list[0].pk,
    )
    second_reference = AttributeValue.objects.create(
        attribute=page_type_variant_reference_attribute,
        slug=f"{page.pk}_{product_variant_list[1].pk}",
        reference_variant_id=product_variant_list[1].pk,
    )

    associate_attribute_values_to_instance(
        page,
        {page_type_variant_reference_attribute.pk: [first_reference, second_reference]},
    )

    assert page.attributevalues.count() == 3
    expected_value_limit = 1

    # when
    response = staff_api_client.post_graphql(
        ASSIGNED_MULTIPLE_PRODUCT_VARIANT_REFERENCE_ATTRIBUTE_QUERY,
        variables={
            "id": graphene.Node.to_global_id("Page", page.pk),
            "valueLimit": expected_value_limit,
        },
    )

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["page"]["assignedAttributes"]) == 1
    assert (
        len(content["data"]["page"]["assignedAttributes"][0]["value"])
        == expected_value_limit
    )
    assert (
        content["data"]["page"]["assignedAttributes"][0]["value"][0]["sku"]
        == first_reference.reference_variant.sku
    )


ASSIGNED_MULTIPLE_CATEGORY_REFERENCE_ATTRIBUTE_QUERY = """
query PageQuery($id: ID, $valueLimit: PositiveInt) {
  page(id: $id) {
    assignedAttributes(limit:10) {
      ...on AssignedMultiCategoryReferenceAttribute{
        __typename
        value(limit: $valueLimit) {
          __typename
          slug
        }
      }
    }
  }
}
"""


def test_assigned_multi_category_reference_attribute(
    staff_api_client,
    page,
    category,
    page_type_category_reference_attribute,
):
    # given
    referenced_category = category
    expected_reference_slug = "referenced-category-slug"
    referenced_category.slug = expected_reference_slug
    referenced_category.save(update_fields=["slug"])

    page_type_category_reference_attribute.input_type = AttributeInputType.REFERENCE
    page_type_category_reference_attribute.save()
    page_type = page.page_type
    page_type.page_attributes.set([page_type_category_reference_attribute])

    attr_value = AttributeValue.objects.create(
        attribute=page_type_category_reference_attribute,
        slug=f"{page.pk}_{referenced_category.pk}",
        reference_category_id=referenced_category.pk,
    )

    associate_attribute_values_to_instance(
        page, {page_type_category_reference_attribute.pk: [attr_value]}
    )

    # when
    response = staff_api_client.post_graphql(
        ASSIGNED_MULTIPLE_CATEGORY_REFERENCE_ATTRIBUTE_QUERY,
        variables={"id": graphene.Node.to_global_id("Page", page.pk)},
    )

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["page"]["assignedAttributes"]) == 1

    data = content["data"]["page"]["assignedAttributes"][0]["value"]
    assert len(data) == 1
    single_page_data = data[0]
    assert single_page_data["__typename"] == "Category"
    assert single_page_data["slug"] == expected_reference_slug


def test_applies_limit_to_multi_category_references(
    staff_api_client,
    page,
    categories,
    page_type_category_reference_attribute,
):
    # given
    page_type = page.page_type

    # make sure that our attribute is on first position
    page_type.page_attributes.update(storefront_search_position=10)
    page_type.page_attributes.set([page_type_category_reference_attribute])
    page_type_category_reference_attribute.input_type = AttributeInputType.REFERENCE
    page_type_category_reference_attribute.storefront_search_position = 1
    page_type_category_reference_attribute.save()

    first_reference = AttributeValue.objects.create(
        attribute=page_type_category_reference_attribute,
        slug=f"{page.pk}_{categories[0].pk}",
        reference_category_id=categories[0].pk,
    )
    second_reference = AttributeValue.objects.create(
        attribute=page_type_category_reference_attribute,
        slug=f"{page.pk}_{categories[1].pk}",
        reference_category_id=categories[1].pk,
    )

    associate_attribute_values_to_instance(
        page,
        {
            page_type_category_reference_attribute.pk: [
                first_reference,
                second_reference,
            ]
        },
    )

    assert page.attributevalues.count() == 3
    expected_value_limit = 1

    # when
    response = staff_api_client.post_graphql(
        ASSIGNED_MULTIPLE_CATEGORY_REFERENCE_ATTRIBUTE_QUERY,
        variables={
            "id": graphene.Node.to_global_id("Page", page.pk),
            "valueLimit": expected_value_limit,
        },
    )

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["page"]["assignedAttributes"]) == 1
    assert (
        len(content["data"]["page"]["assignedAttributes"][0]["value"])
        == expected_value_limit
    )
    assert (
        content["data"]["page"]["assignedAttributes"][0]["value"][0]["slug"]
        == first_reference.reference_category.slug
    )


ASSIGNED_MULTIPLE_COLLECTION_REFERENCE_ATTRIBUTE_QUERY = """
query PageQuery($id: ID, $valueLimit: PositiveInt) {
  page(id: $id) {
    assignedAttributes(limit:10) {
      ...on AssignedMultiCollectionReferenceAttribute{
        __typename
        value(limit: $valueLimit) {
          __typename
          slug
        }
      }
    }
  }
}
"""


def test_assigned_multi_collection_reference_attribute(
    staff_api_client,
    page,
    collection,
    page_type_collection_reference_attribute,
):
    # given
    referenced_collection = collection
    expected_reference_slug = "referenced-collection-slug"
    referenced_collection.slug = expected_reference_slug
    referenced_collection.save(update_fields=["slug"])

    page_type_collection_reference_attribute.input_type = AttributeInputType.REFERENCE
    page_type_collection_reference_attribute.save()
    page_type = page.page_type
    page_type.page_attributes.set([page_type_collection_reference_attribute])

    attr_value = AttributeValue.objects.create(
        attribute=page_type_collection_reference_attribute,
        slug=f"{page.pk}_{referenced_collection.pk}",
        reference_collection_id=referenced_collection.pk,
    )

    associate_attribute_values_to_instance(
        page, {page_type_collection_reference_attribute.pk: [attr_value]}
    )

    # when
    response = staff_api_client.post_graphql(
        ASSIGNED_MULTIPLE_COLLECTION_REFERENCE_ATTRIBUTE_QUERY,
        variables={"id": graphene.Node.to_global_id("Page", page.pk)},
    )

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["page"]["assignedAttributes"]) == 1

    data = content["data"]["page"]["assignedAttributes"][0]["value"]
    assert len(data) == 1
    single_page_data = data[0]
    assert single_page_data["__typename"] == "Collection"
    assert single_page_data["slug"] == expected_reference_slug


def test_applies_limit_to_multi_collection_references(
    staff_api_client,
    page,
    published_collections,
    page_type_collection_reference_attribute,
):
    # given
    page_type = page.page_type
    # make sure that our attribute is on first position
    page_type.page_attributes.update(storefront_search_position=10)
    page_type.page_attributes.set([page_type_collection_reference_attribute])
    page_type_collection_reference_attribute.input_type = AttributeInputType.REFERENCE
    page_type_collection_reference_attribute.storefront_search_position = 1
    page_type_collection_reference_attribute.save()

    first_reference = AttributeValue.objects.create(
        attribute=page_type_collection_reference_attribute,
        slug=f"{page.pk}_{published_collections[0].pk}",
        reference_collection_id=published_collections[0].pk,
    )
    second_reference = AttributeValue.objects.create(
        attribute=page_type_collection_reference_attribute,
        slug=f"{page.pk}_{published_collections[1].pk}",
        reference_collection_id=published_collections[1].pk,
    )

    associate_attribute_values_to_instance(
        page,
        {
            page_type_collection_reference_attribute.pk: [
                first_reference,
                second_reference,
            ]
        },
    )

    assert page.attributevalues.count() == 3
    expected_value_limit = 1

    # when
    response = staff_api_client.post_graphql(
        ASSIGNED_MULTIPLE_COLLECTION_REFERENCE_ATTRIBUTE_QUERY,
        variables={
            "id": graphene.Node.to_global_id("Page", page.pk),
            "valueLimit": expected_value_limit,
        },
    )

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["page"]["assignedAttributes"]) == 1
    assert (
        len(content["data"]["page"]["assignedAttributes"][0]["value"])
        == expected_value_limit
    )
    assert (
        content["data"]["page"]["assignedAttributes"][0]["value"][0]["slug"]
        == first_reference.reference_collection.slug
    )


ASSIGNED_SINGLE_CHOICE_ATTRIBUTE_QUERY = """
query PageQuery($id: ID) {
  page(id: $id) {
    assignedAttributes(limit:10) {
      ...on AssignedSingleChoiceAttribute{
        __typename
        value{
          name
          slug
          translation(languageCode:FR)
        }
      }
    }
  }
}
"""


def test_assigned_single_choice_attribute_translation(
    staff_api_client,
    page,
    size_page_attribute,
):
    # given
    page_type = page.page_type
    page_type.page_attributes.set([size_page_attribute])

    attr_value = size_page_attribute.values.first()
    translation = AttributeValueTranslation.objects.create(
        language_code="fr",
        attribute_value=attr_value,
        name="French Size Name",
    )

    associate_attribute_values_to_instance(page, {size_page_attribute.pk: [attr_value]})

    # when
    response = staff_api_client.post_graphql(
        ASSIGNED_SINGLE_CHOICE_ATTRIBUTE_QUERY,
        variables={"id": graphene.Node.to_global_id("Page", page.pk)},
    )

    # then
    content = get_graphql_content(response)

    assert len(content["data"]["page"]["assignedAttributes"]) == 1
    assert (
        content["data"]["page"]["assignedAttributes"][0]["value"]["translation"]
        == translation.name
    )


def test_assigned_single_choice_attribute(
    staff_api_client,
    page,
    size_page_attribute,
):
    # given
    page_type = page.page_type
    page_type.page_attributes.set([size_page_attribute])

    attr_value = size_page_attribute.values.first()
    expected_attr_value_name = "Size M"
    expected_attr_value_slug = "size-m"
    attr_value.slug = expected_attr_value_slug
    attr_value.name = expected_attr_value_name
    attr_value.save()

    associate_attribute_values_to_instance(page, {size_page_attribute.pk: [attr_value]})

    # when
    response = staff_api_client.post_graphql(
        ASSIGNED_SINGLE_CHOICE_ATTRIBUTE_QUERY,
        variables={"id": graphene.Node.to_global_id("Page", page.pk)},
    )

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["page"]["assignedAttributes"]) == 1
    attr_value_data = content["data"]["page"]["assignedAttributes"][0]["value"]
    assert attr_value_data["name"] == expected_attr_value_name
    assert attr_value_data["slug"] == expected_attr_value_slug


ASSIGNED_MULTI_CHOICE_ATTRIBUTE_QUERY = """
query PageQuery($id: ID, $valueLimit: PositiveInt) {
  page(id: $id) {
    assignedAttributes(limit:10) {
      ... on AssignedMultiChoiceAttribute {
        __typename
        value(limit: $valueLimit) {
          name
          slug
          translation(languageCode: FR)
        }
      }
    }
  }
}
"""


def test_assigned_multi_choice_attribute_translation(
    staff_api_client,
    page,
    size_page_attribute,
):
    # given
    page_type = page.page_type
    page_type.page_attributes.set([size_page_attribute])

    size_page_attribute.input_type = AttributeInputType.MULTISELECT
    size_page_attribute.save()

    attr_value = size_page_attribute.values.first()
    translation = AttributeValueTranslation.objects.create(
        language_code="fr",
        attribute_value=attr_value,
        name="French Size Name",
    )

    associate_attribute_values_to_instance(page, {size_page_attribute.pk: [attr_value]})

    # when
    response = staff_api_client.post_graphql(
        ASSIGNED_MULTI_CHOICE_ATTRIBUTE_QUERY,
        variables={"id": graphene.Node.to_global_id("Page", page.pk)},
    )

    # then
    content = get_graphql_content(response)

    assert len(content["data"]["page"]["assignedAttributes"]) == 1
    assert len(content["data"]["page"]["assignedAttributes"][0]["value"]) == 1
    attr_value_data = content["data"]["page"]["assignedAttributes"][0]["value"][0]
    assert attr_value_data["translation"] == translation.name


def test_applies_limit_to_multi_choices(
    staff_api_client,
    page,
    size_page_attribute,
):
    # given
    page_type = page.page_type
    page_type.page_attributes.set([size_page_attribute])

    size_page_attribute.input_type = AttributeInputType.MULTISELECT
    size_page_attribute.save()

    first_choice = size_page_attribute.values.first()
    second_choice = size_page_attribute.values.last()

    associate_attribute_values_to_instance(
        page, {size_page_attribute.pk: [first_choice, second_choice]}
    )

    assert page.attributevalues.count() == 2
    expected_value_limit = 1

    # when
    response = staff_api_client.post_graphql(
        ASSIGNED_MULTI_CHOICE_ATTRIBUTE_QUERY,
        variables={
            "id": graphene.Node.to_global_id("Page", page.pk),
            "valueLimit": expected_value_limit,
        },
    )

    # then
    content = get_graphql_content(response)

    assert len(content["data"]["page"]["assignedAttributes"]) == 1
    assert (
        len(content["data"]["page"]["assignedAttributes"][0]["value"])
        == expected_value_limit
    )
    assert (
        content["data"]["page"]["assignedAttributes"][0]["value"][0]["slug"]
        == first_choice.slug
    )


def test_assigned_multi_choice_attribute(
    staff_api_client,
    page,
    size_page_attribute,
):
    # given
    page_type = page.page_type
    page_type.page_attributes.set([size_page_attribute])

    size_page_attribute.input_type = AttributeInputType.MULTISELECT
    size_page_attribute.save()

    attr_value = size_page_attribute.values.first()
    expected_attr_value_name = "Size M"
    expected_attr_value_slug = "size-m"
    attr_value.slug = expected_attr_value_slug
    attr_value.name = expected_attr_value_name
    attr_value.save()

    associate_attribute_values_to_instance(page, {size_page_attribute.pk: [attr_value]})

    # when
    response = staff_api_client.post_graphql(
        ASSIGNED_MULTI_CHOICE_ATTRIBUTE_QUERY,
        variables={"id": graphene.Node.to_global_id("Page", page.pk)},
    )

    # then
    content = get_graphql_content(response)

    assert len(content["data"]["page"]["assignedAttributes"]) == 1
    assert len(content["data"]["page"]["assignedAttributes"][0]["value"]) == 1
    attr_value_data = content["data"]["page"]["assignedAttributes"][0]["value"][0]
    assert attr_value_data["name"] == expected_attr_value_name
    assert attr_value_data["slug"] == expected_attr_value_slug


ASSIGNED_SWATCH_ATTRIBUTE_QUERY = """
query PageQuery($id: ID) {
  page(id: $id) {
    assignedAttributes(limit:10) {
      ... on AssignedSwatchAttribute {
        value {
          name
          slug
          hexColor
          file {
            url
            contentType
          }
        }
      }
    }
  }
}
"""


def test_assigned_swatch_attribute(
    staff_api_client,
    page,
    swatch_attribute,
):
    # given
    swatch_attribute.type = AttributeType.PAGE_TYPE
    swatch_attribute.save()

    page_type = page.page_type
    page_type.page_attributes.set([swatch_attribute])

    attr_value = swatch_attribute.values.first()
    expected_attr_value_name = "Red"
    expected_attr_value_slug = "red"
    expected_attr_hex_value = "#5C3030"
    attr_value.slug = expected_attr_value_slug
    attr_value.name = expected_attr_value_name
    attr_value.value = expected_attr_hex_value
    attr_value.save()

    associate_attribute_values_to_instance(page, {swatch_attribute.pk: [attr_value]})

    # when
    response = staff_api_client.post_graphql(
        ASSIGNED_SWATCH_ATTRIBUTE_QUERY,
        variables={"id": graphene.Node.to_global_id("Page", page.pk)},
    )

    # then
    content = get_graphql_content(response)

    assert len(content["data"]["page"]["assignedAttributes"]) == 1
    attr_value_data = content["data"]["page"]["assignedAttributes"][0]["value"]
    assert attr_value_data["name"] == expected_attr_value_name
    assert attr_value_data["slug"] == expected_attr_value_slug
    assert attr_value_data["hexColor"] == expected_attr_hex_value


def test_assigned_swatch_file_attribute(staff_api_client, page, swatch_attribute):
    # given
    swatch_attribute.type = AttributeType.PAGE_TYPE
    swatch_attribute.save()

    page_type = page.page_type
    page_type.page_attributes.set([swatch_attribute])

    attr_value = swatch_attribute.values.first()

    attr_value.file_url = "https://example.com/file.pdf"
    attr_value.content_type = "application/pdf"
    attr_value.save()

    associate_attribute_values_to_instance(page, {swatch_attribute.pk: [attr_value]})

    assert attr_value.file_url is not None

    # when
    response = staff_api_client.post_graphql(
        ASSIGNED_SWATCH_ATTRIBUTE_QUERY,
        variables={"id": graphene.Node.to_global_id("Page", page.pk)},
    )

    # then
    content = get_graphql_content(response)

    assert len(content["data"]["page"]["assignedAttributes"]) == 1
    attr_value_data = content["data"]["page"]["assignedAttributes"][0]["value"]
    assert attr_value_data["name"] == attr_value.name
    assert attr_value_data["slug"] == attr_value.slug
    assert attr_value_data["file"]["url"] == attr_value.file_url
    assert attr_value_data["file"]["contentType"] == attr_value.content_type


ASSIGNED_BOOLEAN_ATTRIBUTE_QUERY = """
query PageQuery($id: ID) {
  page(id: $id) {
    assignedAttributes(limit:10) {
      ... on AssignedBooleanAttribute {
        value
      }
    }
  }
}
"""


def test_assigned_boolean_attribute(
    staff_api_client,
    page,
    boolean_attribute,
):
    # given
    boolean_attribute.type = AttributeType.PAGE_TYPE
    boolean_attribute.save()

    page_type = page.page_type
    page_type.page_attributes.set([boolean_attribute])

    attr_value = boolean_attribute.values.first()
    expected_attr_value = True
    attr_value.boolean = expected_attr_value
    attr_value.save()

    associate_attribute_values_to_instance(page, {boolean_attribute.pk: [attr_value]})

    # when
    response = staff_api_client.post_graphql(
        ASSIGNED_BOOLEAN_ATTRIBUTE_QUERY,
        variables={"id": graphene.Node.to_global_id("Page", page.pk)},
    )

    # then
    content = get_graphql_content(response)

    assert len(content["data"]["page"]["assignedAttributes"]) == 1
    attr_value_data = content["data"]["page"]["assignedAttributes"][0]["value"]
    assert attr_value_data is expected_attr_value


ASSIGNED_DATE_ATTRIBUTE_QUERY = """
query PageQuery($id: ID) {
  page(id: $id) {
    assignedAttributes(limit:10) {
      ... on AssignedDateAttribute {
        value
      }
    }
  }
}
"""


def test_assigned_date_attribute(
    staff_api_client,
    page,
    date_attribute,
):
    # given
    date_attribute.type = AttributeType.PAGE_TYPE
    date_attribute.save()

    page_type = page.page_type
    page_type.page_attributes.set([date_attribute])

    attr_value = date_attribute.values.first()
    expected_attr_datetime_value = datetime.now(UTC)
    attr_value.date_time = expected_attr_datetime_value
    attr_value.save()

    associate_attribute_values_to_instance(page, {date_attribute.pk: [attr_value]})

    # when
    response = staff_api_client.post_graphql(
        ASSIGNED_DATE_ATTRIBUTE_QUERY,
        variables={"id": graphene.Node.to_global_id("Page", page.pk)},
    )

    # then
    content = get_graphql_content(response)

    assert len(content["data"]["page"]["assignedAttributes"]) == 1
    attr_value_data = content["data"]["page"]["assignedAttributes"][0]["value"]
    assert attr_value_data == str(expected_attr_datetime_value.date())


ASSIGNED_DATETIME_ATTRIBUTE_QUERY = """
query PageQuery($id: ID) {
  page(id: $id) {
    assignedAttributes(limit:10) {
      ... on AssignedDateTimeAttribute {
        value
      }
    }
  }
}
"""


def test_assigned_datetime_attribute(
    staff_api_client,
    page,
    date_time_attribute,
):
    # given
    date_time_attribute.type = AttributeType.PAGE_TYPE
    date_time_attribute.save()

    page_type = page.page_type
    page_type.page_attributes.set([date_time_attribute])

    attr_value = date_time_attribute.values.first()
    expected_attr_datetime_value = datetime.now(UTC)
    attr_value.date_time = expected_attr_datetime_value
    attr_value.save()

    associate_attribute_values_to_instance(page, {date_time_attribute.pk: [attr_value]})

    # when
    response = staff_api_client.post_graphql(
        ASSIGNED_DATETIME_ATTRIBUTE_QUERY,
        variables={"id": graphene.Node.to_global_id("Page", page.pk)},
    )

    # then
    content = get_graphql_content(response)

    assert len(content["data"]["page"]["assignedAttributes"]) == 1
    attr_value_data = content["data"]["page"]["assignedAttributes"][0]["value"]
    assert attr_value_data == str(expected_attr_datetime_value.isoformat())


def test_all_non_reference_attribute_type_has_own_assigned_types():
    expected_attribute_types = [value for (value, _) in AttributeInputType.CHOICES]
    expected_attribute_types.remove(
        AttributeInputType.SINGLE_REFERENCE,
    )
    expected_attribute_types.remove(
        AttributeInputType.REFERENCE,
    )

    assert all(ASSIGNED_ATTRIBUTE_MAP.values())
    assert set(ASSIGNED_ATTRIBUTE_MAP.keys()) == set(expected_attribute_types)


def test_all_single_reference_attribute_type_has_own_assigned_types():
    expected_entity_names = [
        entity_name for (entity_name, _) in AttributeEntityType.CHOICES
    ]

    assert all(ASSIGNED_SINGLE_REFERENCE_MAP.values())
    assert set(ASSIGNED_SINGLE_REFERENCE_MAP.keys()) == set(expected_entity_names)


def test_all_multi_reference_attribute_type_has_own_assigned_types():
    expected_entity_names = [
        entity_name for (entity_name, _) in AttributeEntityType.CHOICES
    ]

    assert all(ASSIGNED_MULTI_REFERENCE_MAP.values())
    assert set(ASSIGNED_MULTI_REFERENCE_MAP.keys()) == set(expected_entity_names)
