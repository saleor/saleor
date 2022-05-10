import graphene
import pytest

from .....attribute.utils import associate_attribute_values_to_instance

ATTRIBUTE_VALUE_DELETE_MUTATION = """
    mutation AttributeValueDelete($id: ID!) {
        attributeValueDelete(id: $id) {
            attributeValue {
                name
                slug
            }
        }
    }
"""


def test_delete_attribute_value(
    staff_api_client,
    color_attribute,
    pink_attribute_value,
    permission_manage_product_types_and_attributes,
):
    # given
    value = color_attribute.values.get(name="Red")
    query = ATTRIBUTE_VALUE_DELETE_MUTATION
    node_id = graphene.Node.to_global_id("AttributeValue", value.id)
    variables = {"id": node_id}

    # when
    staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    with pytest.raises(value._meta.model.DoesNotExist):
        value.refresh_from_db()


def test_delete_file_attribute_value(
    staff_api_client,
    file_attribute,
    permission_manage_product_types_and_attributes,
):
    # given
    value = file_attribute.values.first()
    query = ATTRIBUTE_VALUE_DELETE_MUTATION
    node_id = graphene.Node.to_global_id("AttributeValue", value.id)
    variables = {"id": node_id}

    # when
    staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    with pytest.raises(value._meta.model.DoesNotExist):
        value.refresh_from_db()


def test_delete_attribute_value_product_search_document_updated(
    staff_api_client,
    color_attribute,
    permission_manage_product_types_and_attributes,
    product,
):
    # given
    attribute = color_attribute
    name = "Red"
    value = color_attribute.values.get(name=name)

    product_type = product.product_type
    product_type.product_attributes.add(attribute)

    associate_attribute_values_to_instance(product, attribute, value)

    query = ATTRIBUTE_VALUE_DELETE_MUTATION
    node_id = graphene.Node.to_global_id("AttributeValue", value.id)
    variables = {"id": node_id}

    # when
    staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    with pytest.raises(value._meta.model.DoesNotExist):
        value.refresh_from_db()


def test_delete_attribute_value_product_search_document_updated_variant_attribute(
    staff_api_client,
    color_attribute,
    permission_manage_product_types_and_attributes,
    variant,
):
    # given
    name = "Red"
    attribute = color_attribute
    value = color_attribute.values.get(name=name)

    product = variant.product
    product_type = product.product_type
    product_type.variant_attributes.add(attribute)

    associate_attribute_values_to_instance(variant, attribute, value)

    query = ATTRIBUTE_VALUE_DELETE_MUTATION
    node_id = graphene.Node.to_global_id("AttributeValue", value.id)
    variables = {"id": node_id}

    # when
    staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    with pytest.raises(value._meta.model.DoesNotExist):
        value.refresh_from_db()
