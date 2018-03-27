import json
from unittest.mock import patch

import graphene
import pytest
from django.shortcuts import reverse

from saleor.dashboard.graphql.mutations import (
    ModelFormMutation, ModelFormUpdateMutation)

from ..utils import get_graphql_content


@patch('saleor.dashboard.graphql.mutations.convert_form_fields')
@patch('saleor.dashboard.graphql.mutations.convert_form_field')
def test_model_form_mutation(
        mocked_convert_form_field, mocked_convert_form_fields,
        model_form_class):

    mocked_convert_form_fields.return_value = {
        model_form_class._meta.fields: mocked_convert_form_field.return_value}

    class TestMutation(ModelFormMutation):
        test_field = graphene.String()

        class Arguments:
            test_input = graphene.String()

        class Meta:
            form_class = model_form_class
            return_field_name = 'test_return_field'

    meta = TestMutation._meta
    assert meta.form_class == model_form_class
    assert meta.model == 'test_model'
    assert meta.return_field_name == 'test_return_field'
    arguments = meta.arguments
    # check if declarative arguments are present
    assert 'test_input' in arguments
    # check if model form field is present
    mocked_convert_form_fields.assert_called_with(model_form_class, None)
    assert 'test_field' in arguments

    output_fields = meta.fields
    assert 'test_return_field' in output_fields
    assert 'errors' in output_fields


@patch('saleor.dashboard.graphql.mutations')
def test_model_form_update_mutation(model_form_class):
    class TestUpdateMutation(ModelFormUpdateMutation):
        class Meta:
            form_class = model_form_class
            return_field_name = 'test_return_field'

    meta = TestUpdateMutation._meta
    assert 'id' in meta.arguments


def test_category_create_mutation(admin_client):
    query = """
        mutation($name: String!, $description: String, $parentId: ID) {
            categoryCreate(
                name: $name
                description: $description
                parentId: $parentId
            ) {
                category {
                    id
                    name
                    slug
                    description
                    parent {
                        name
                        id
                    }
                }
                errors {
                    field
                    message
                }
            }
        }
    """

    category_name = 'Test category'
    category_description = 'Test description'

    # test creating root category
    variables = json.dumps({
        'name': category_name, 'description': category_description})
    response = admin_client.post(
        reverse('dashboard:api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['categoryCreate']
    assert data['errors'] == []
    assert data['category']['name'] == category_name
    assert data['category']['description'] == category_description
    assert not data['category']['parent']

    # test creating subcategory
    parent_id = data['category']['id']
    variables = json.dumps({
        'name': category_name, 'description': category_description,
        'parentId': parent_id})
    response = admin_client.post(
        reverse('dashboard:api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['categoryCreate']
    assert data['errors'] == []
    assert data['category']['parent']['id'] == parent_id


def test_category_update_mutation(admin_client, default_category):
    query = """
        mutation($id: ID, $name: String!, $description: String) {
            categoryUpdate(
                id: $id
                name: $name
                description: $description
            ) {
                category {
                    id
                    name
                    description
                    parent {
                        id
                    }
                }
                errors {
                    field
                    message
                }
            }
        }
    """
    # create child category and test that the update mutation won't change
    # it's parent
    child_category = default_category.children.create(name='child')

    category_name = 'Updated name'
    category_description = 'Updated description'

    category_id = graphene.Node.to_global_id('Category', child_category.pk)
    variables = json.dumps({
        'name': category_name, 'description': category_description,
        'id': category_id})
    response = admin_client.post(
        reverse('dashboard:api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['categoryUpdate']
    assert data['errors'] == []
    assert data['category']['id'] == category_id
    assert data['category']['name'] == category_name
    assert data['category']['description'] == category_description

    parent_id = graphene.Node.to_global_id('Category', default_category.pk)
    assert data['category']['parent']['id'] == parent_id


def test_category_delete_mutation(admin_client, default_category):
    query = """
        mutation($id: ID!) {
            categoryDelete(id: $id) {
                category {
                    name
                }
                errors {
                    field
                    message
                }
            }
        }
    """
    variables = json.dumps({
        'id': graphene.Node.to_global_id('Category', default_category.id)})
    response = admin_client.post(
        reverse('dashboard:api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['categoryDelete']
    assert data['category']['name'] == default_category.name
    with pytest.raises(default_category._meta.model.DoesNotExist):
        default_category.refresh_from_db()


def test_page_create_mutation(admin_client):
    query = """
        mutation CreatePage(
            $slug: String!,
            $title: String!,
            $content: String!,
            $isVisible: Boolean!) {
                pageCreate(slug: $slug,
                title: $title,
                content: $content,
                isVisible: $isVisible) {
                    page {
                        id
                        title
                        content
                        slug
                        isVisible
                      }
                      errors {
                        message
                        field
                      }
                    }
                  }
    """
    page_slug = 'test-slug'
    page_content = 'test content'
    page_title = 'test title'
    page_isVisible = True

    # test creating root page
    variables = json.dumps({
        'title': page_title, 'content': page_content,
        'isVisible': page_isVisible, 'slug': page_slug})
    response = admin_client.post(
        reverse('dashboard:api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['pageCreate']
    assert data['errors'] == []
    assert data['page']['title'] == page_title
    assert data['page']['content'] == page_content
    assert data['page']['slug'] == page_slug
    assert data['page']['isVisible'] == page_isVisible


def test_page_delete_mutation(admin_client, page):
    query = """
        mutation DeletePage($id: ID!) {
            pageDelete(id: $id) {
                page {
                    title
                    id
                }
                errors {
                    field
                    message
                }
              }
            }
    """
    variables = json.dumps({
        'id': graphene.Node.to_global_id('Page', page.id)})
    response = admin_client.post(
        reverse('dashboard:api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['pageDelete']
    assert data['page']['title'] == page.title
    with pytest.raises(page._meta.model.DoesNotExist):
        page.refresh_from_db()


def test_create_product(
        client, product_type, default_category, size_attribute):
    query = """
        mutation createProduct(
            $productTypeId: ID!,
            $categoryId: ID!
            $name: String!,
            $description: String!,
            $isPublished: Boolean!,
            $isFeatured: Boolean!,
            $price: Float!,
            $attributes: [ValuesInput]) {
                productCreate(
                    categoryId: $categoryId,
                    productTypeId: $productTypeId,
                    name: $name,
                    description: $description,
                    isPublished: $isPublished,
                    isFeatured: $isFeatured,
                    price: $price,
                    attributes: $attributes) {
                        product {
                            category{
                                name
                            }
                            description
                            isPublished
                            isFeatured
                            name
                            price{
                                amount
                            }
                            productType{
                                name
                            }
                            attributes{
                                name
                                value
                            }
                          }
                          errors {
                            message
                            field
                          }
                        }
                      }
    """

    product_type_id = graphene.Node.to_global_id(
        'ProductType', product_type.pk)
    category_id = graphene.Node.to_global_id(
        'Category', default_category.pk)
    product_description = 'test description'
    product_name = 'test name'
    product_isPublished = True
    product_isFeatured = False
    product_price = 22

    # Default attribute defined in product_type fixture
    color_attr = product_type.product_attributes.get(name='Color')
    color_attr_name = color_attr.name
    color_attr_value = color_attr.values.first().name
    color_attr_slug = color_attr.values.first().slug
    # Add second attribute
    product_type.product_attributes.add(size_attribute)
    size_attr_name = product_type.product_attributes.get(name='Size').name
    non_existent_attr_value = 'The cake is a lie'

    # test creating root product
    variables = json.dumps({
        'productTypeId': product_type_id,
        'categoryId': category_id,
        'name': product_name,
        'description': product_description,
        'isPublished': product_isPublished,
        'isFeatured': product_isFeatured,
        'price': product_price,
        'attributes': [
            {'name': color_attr_name, 'value': color_attr_value},
            {'name': size_attr_name, 'value': non_existent_attr_value}]})

    response = client.post(
        reverse('dashboard:api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['productCreate']
    assert data['errors'] == []
    assert data['product']['name'] == product_name
    assert data['product']['description'] == product_description
    assert data['product']['isFeatured'] == product_isFeatured
    assert data['product']['isPublished'] == product_isPublished
    assert data['product']['productType']['name'] == product_type.name
    assert data['product']['category']['name'] == default_category.name
    assert data['product']['attributes'][1]['value'] == None
    assert data['product']['attributes'][0]['value'] == color_attr_slug


def test_update_product(
    client, default_category, non_default_category, product_in_stock):
    query = """
        mutation updateProduct(
            $productId: ID!,
            $categoryId: ID,
            $name: String!,
            $description: String!,
            $isPublished: Boolean!,
            $isFeatured: Boolean!,
            $price: Float!,
            $attributes: [ValuesInput]) {
                productUpdate(
                    categoryId: $categoryId,
                    id: $productId,
                    name: $name,
                    description: $description,
                    isPublished: $isPublished,
                    isFeatured: $isFeatured,
                    price: $price,
                    attributes: $attributes) {
                        product {
                            category{
                                name
                            }
                            description
                            isPublished
                            isFeatured
                            name
                            price{
                                amount
                            }
                            productType{
                                name
                            }
                            attributes{
                                name
                                value
                            }
                          }
                          errors {
                            message
                            field
                          }
                        }
                      }
    """
    product_id = graphene.Node.to_global_id('Product', product_in_stock.pk)
    category_id = graphene.Node.to_global_id(
        'Category', non_default_category.pk)
    product_description = 'updated description'
    product_name = 'updated name'
    product_isPublished = True
    product_isFeatured = False
    product_price = 33

    variables = json.dumps({
        'productId': product_id,
        'categoryId': category_id,
        'name': product_name,
        'description': product_description,
        'isPublished': product_isPublished,
        'isFeatured': product_isFeatured,
        'price': product_price})

    response = client.post(
        reverse('dashboard:api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['productUpdate']
    assert data['errors'] == []
    assert data['product']['name'] == product_name
    assert data['product']['description'] == product_description
    assert data['product']['isFeatured'] == product_isFeatured
    assert data['product']['isPublished'] == product_isPublished
    assert not data['product']['category']['name'] == default_category.name


def test_delete_product(client, product_in_stock):
    query = """
        mutation DeleteProduct($id: ID!) {
            productDelete(id: $id) {
                product {
                    name
                    id
                }
                errors {
                    field
                    message
                }
              }
            }
    """
    variables = json.dumps({
        'id': graphene.Node.to_global_id('Product', product_in_stock.id)})
    response = client.post(
        reverse('dashboard:api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['productDelete']
    assert data['product']['name'] == product_in_stock.name
    with pytest.raises(product_in_stock._meta.model.DoesNotExist):
        product_in_stock.refresh_from_db()
