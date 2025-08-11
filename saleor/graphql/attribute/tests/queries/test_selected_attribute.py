import graphene

from .....attribute.models.base import AttributeValue, AttributeValueTranslation
from .....attribute.utils import associate_attribute_values_to_instance
from ....tests.utils import get_graphql_content

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
    attributes {
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

    assert len(content["data"]["page"]["attributes"]) == 1
    assert content["data"]["page"]["attributes"][0]["value"] == attr_value.numeric


ASSIGNED_TEXT_ATTRIBUTE_QUERY = """
query PageQuery($id: ID) {
  page(id: $id) {
    attributes {
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

    assert len(content["data"]["page"]["attributes"]) == 1
    assert (
        content["data"]["page"]["attributes"][0]["translation"]
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

    assert len(content["data"]["page"]["attributes"]) == 1
    assert content["data"]["page"]["attributes"][0]["value"] == attr_value.rich_text


ASSIGNED_PLAIN_TEXT_ATTRIBUTE_QUERY = """
query PageQuery($id: ID) {
  page(id: $id) {
    attributes {
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

    assert len(content["data"]["page"]["attributes"]) == 1
    assert (
        content["data"]["page"]["attributes"][0]["translation"]
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

    assert len(content["data"]["page"]["attributes"]) == 1
    assert content["data"]["page"]["attributes"][0]["value"] == attr_value.plain_text


ASSIGNED_FILE_ATTRIBUTE_QUERY = """
query PageQuery($id: ID) {
  page(id: $id) {
    attributes {
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

    assert len(content["data"]["page"]["attributes"]) == 1
    assert (
        content["data"]["page"]["attributes"][0]["value"]["url"] == attr_value.file_url
    )
    assert (
        content["data"]["page"]["attributes"][0]["value"]["contentType"]
        == attr_value.content_type
    )
