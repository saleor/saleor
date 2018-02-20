import json

import graphene
import pytest
from django import forms
from django.shortcuts import reverse

from saleor.dashboard.category.forms import CategoryForm
from saleor.dashboard.graphql.mutations import (
    ModelFormMutation, ModelFormUpdateMutation)
from saleor.product.models import Category, Product, ProductAttribute

from ..utils import get_graphql_content


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']


def test_model_form_mutation():
    class CategoryMutation(ModelFormMutation):
        test_field = graphene.String()

        class Arguments:
            test_input = graphene.String()

        class Meta:
            form_class = CategoryForm
            return_field_name = 'category'

    meta = CategoryMutation._meta
    assert meta.form_class == CategoryForm
    assert meta.model == CategoryForm._meta.model
    assert meta.return_field_name == 'category'

    arguments = meta.arguments
    # check if declarative arguments are present
    assert 'test_input' in arguments
    # check if model form field is present
    assert 'name' in arguments

    output_fields = meta.fields
    assert 'category' in output_fields
    assert 'errors' in output_fields


def test_model_form_update_mutation():
    class CategoryUpdateMutation(ModelFormUpdateMutation):
        class Meta:
            form_class = CategoryForm

    meta = CategoryUpdateMutation._meta
    assert 'id' in meta.arguments


def test_category_create_mutation(client):
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
    response = client.post(
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
    response = client.post(
        reverse('dashboard:api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['categoryCreate']
    assert data['errors'] == []
    assert data['category']['parent']['id'] == parent_id


def test_category_update_mutation(client, default_category):
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
    response = client.post(
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


def test_category_delete_mutation(client, default_category):
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
    response = client.post(
        reverse('dashboard:api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['categoryDelete']
    assert data['category']['name'] == default_category.name
    with pytest.raises(Category.DoesNotExist):
        default_category.refresh_from_db()
