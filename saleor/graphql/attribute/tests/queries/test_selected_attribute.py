import graphene

from .....attribute.models.base import AttributeValue
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
