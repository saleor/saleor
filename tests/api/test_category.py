import json

import graphene
import pytest
from django.shortcuts import reverse
from django.template.defaultfilters import slugify
from tests.utils import get_graphql_content

from saleor.product.models import Category


def test_category_query(user_api_client, product):
    category = Category.objects.first()
    query = '''
    query {
        category(id: "%(category_pk)s") {
            id
            name
            ancestors {
                edges {
                    node {
                        name
                    }
                }
            }
            children {
                edges {
                    node {
                        name
                    }
                }
            }
        }
    }
    ''' % {'category_pk': graphene.Node.to_global_id('Category', category.pk)}
    response = user_api_client.post(reverse('api'), {'query': query})
    content = get_graphql_content(response)
    assert 'errors' not in content
    category_data = content['data']['category']
    assert category_data is not None
    assert category_data['name'] == category.name
    assert (
        len(category_data['ancestors']['edges']) ==
        category.get_ancestors().count())
    assert (
        len(category_data['children']['edges']) ==
        category.get_children().count())


def test_category_create_mutation(admin_api_client):
    query = """
        mutation($name: String, $slug: String, $description: String, $parentId: ID) {
            categoryCreate(
                input: {
                    name: $name
                    slug: $slug
                    description: $description
                    parent: $parentId
                }
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
    category_slug = slugify(category_name)
    category_description = 'Test description'

    # test creating root category
    variables = json.dumps({
        'name': category_name, 'description': category_description,
        'slug': category_slug})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
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
        'parentId': parent_id, 'slug': category_slug})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['categoryCreate']
    assert data['errors'] == []
    assert data['category']['parent']['id'] == parent_id


def test_category_update_mutation(admin_api_client, default_category):
    query = """
        mutation($id: ID!, $name: String, $slug: String, $description: String) {
            categoryUpdate(
                id: $id
                input: {
                    name: $name
                    description: $description
                    slug: $slug
                }
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
    category_slug = slugify(category_name)
    category_description = 'Updated description'

    category_id = graphene.Node.to_global_id('Category', child_category.pk)
    variables = json.dumps({
        'name': category_name, 'description': category_description,
        'id': category_id, 'slug': category_slug})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['categoryUpdate']
    assert data['errors'] == []
    assert data['category']['id'] == category_id
    assert data['category']['name'] == category_name
    assert data['category']['description'] == category_description

    parent_id = graphene.Node.to_global_id('Category', default_category.pk)
    assert data['category']['parent']['id'] == parent_id


def test_category_delete_mutation(admin_api_client, default_category):
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
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['categoryDelete']
    assert data['category']['name'] == default_category.name
    with pytest.raises(default_category._meta.model.DoesNotExist):
        default_category.refresh_from_db()


def test_category_level(user_api_client, default_category):
    category = default_category
    query = """
    query leveled_categories($level: Int) {
        categories(level: $level) {
            edges {
                node {
                    name
                    parent {
                        name
                    }
                }
            }
        }
    }
    """
    child = Category.objects.create(
        name='child', slug='chi-ld', parent=category)
    variables = json.dumps({'level': 0})
    response = user_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    category_data = content['data']['categories']['edges'][0]['node']
    assert category_data['name'] == category.name
    assert category_data['parent'] == None

    query = """
    query leveled_categories($level: Int) {
        categories(level: $level) {
            edges {
                node {
                    name
                    parent {
                        name
                    }
                }
            }
        }
    }
    """
    variables = json.dumps({'level': 1})
    response = user_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    category_data = content['data']['categories']['edges'][0]['node']
    assert category_data['name'] == child.name
    assert category_data['parent']['name'] == category.name
