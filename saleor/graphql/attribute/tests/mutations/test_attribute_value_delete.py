from unittest.mock import patch

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


@patch("saleor.attribute.signals.delete_from_storage_task.delay")
def test_delete_attribute_value(
    delete_from_storage_mock,
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
    delete_from_storage_mock.assert_not_called()


@patch("saleor.attribute.signals.delete_from_storage_task.delay")
def test_delete_file_attribute_value(
    delete_from_storage_mock,
    staff_api_client,
    file_attribute,
    permission_manage_product_types_and_attributes,
):
    # given
    value = file_attribute.values.first()
    file_url = value.file_url
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
    delete_from_storage_mock.assert_called_once_with(file_url)


@patch("saleor.attribute.signals.delete_from_storage_task.delay")
def test_delete_attribute_value_product_search_document_updated(
    delete_from_storage_mock,
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
    delete_from_storage_mock.assert_not_called()

    product.refresh_from_db()
    assert product.search_document
    assert name.lower() not in product.search_document


@patch("saleor.attribute.signals.delete_from_storage_task.delay")
def test_delete_attribute_value_product_search_document_updated_variant_attribute(
    delete_from_storage_mock,
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
    delete_from_storage_mock.assert_not_called()

    product.refresh_from_db()
    assert product.search_document
    assert name.lower() not in product.search_document
