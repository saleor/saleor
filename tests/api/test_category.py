import pytest

import graphene
from django.template.defaultfilters import slugify
from unittest.mock import Mock

from saleor.product.models import Category
from tests.utils import create_image
from tests.api.utils import get_graphql_content, get_multipart_request_body


FETCH_CATEGORY_QUERY = """
query fetchCategory($id: ID!){
    category(id: $id) {
        name
        backgroundImage {
           url(size: 120)
        }
    }
}
"""

LEVELED_CATEGORIES_QUERY = """
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


def test_category_query(user_api_client, product):
    category = Category.objects.first()
    query = """
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
    """ % {'category_pk': graphene.Node.to_global_id('Category', category.pk)}
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    category_data = content['data']['category']
    assert category_data is not None
    assert category_data['name'] == category.name
    assert (
        len(category_data['ancestors']['edges']) ==
        category.get_ancestors().count())
    assert (
        len(category_data['children']['edges']) ==
        category.get_children().count())


def test_category_create_mutation(
        monkeypatch, staff_api_client, permission_manage_products):
    query = """
        mutation($name: String, $slug: String, $description: String, $backgroundImage: Upload, $parentId: ID) {
            categoryCreate(
                input: {
                    name: $name
                    slug: $slug
                    description: $description
                    backgroundImage: $backgroundImage
                },
                parent: $parentId
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

    mock_create_thumbnails = Mock(return_value=None)
    monkeypatch.setattr(
        ('saleor.dashboard.category.forms.'
         'create_category_background_image_thumbnails.delay'),
        mock_create_thumbnails)

    category_name = 'Test category'
    category_slug = slugify(category_name)
    category_description = 'Test description'
    image_file, image_name = create_image()

    # test creating root category
    variables = {
        'name': category_name, 'description': category_description,
        'backgroundImage': image_name, 'slug': category_slug}
    body = get_multipart_request_body(query, variables, image_file, image_name)
    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    data = content['data']['categoryCreate']
    assert data['errors'] == []
    assert data['category']['name'] == category_name
    assert data['category']['description'] == category_description
    assert not data['category']['parent']
    category = Category.objects.get(name=category_name)
    assert category.background_image.file
    mock_create_thumbnails.assert_called_once_with(category.pk)

    # test creating subcategory
    parent_id = data['category']['id']
    variables = {
        'name': category_name, 'description': category_description,
        'parentId': parent_id, 'slug': category_slug}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content['data']['categoryCreate']
    assert data['errors'] == []
    assert data['category']['parent']['id'] == parent_id


def test_category_create_mutation_without_background_image(
        monkeypatch, staff_api_client, permission_manage_products):
    query = """
        mutation($name: String, $slug: String, $description: String, $parentId: ID) {
            categoryCreate(
                input: {
                    name: $name
                    slug: $slug
                    description: $description
                },
                parent: $parentId
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

    mock_create_thumbnails = Mock(return_value=None)
    monkeypatch.setattr(
        ('saleor.dashboard.category.forms.'
         'create_category_background_image_thumbnails.delay'),
        mock_create_thumbnails)

    category_name = 'Test category'
    category_slug = slugify(category_name)
    category_description = 'Test description'

    # test creating root category
    variables = {
        'name': category_name, 'description': category_description,
        'slug': category_slug}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    data = content['data']['categoryCreate']
    assert data['errors'] == []
    assert mock_create_thumbnails.call_count == 0


def test_category_update_mutation(
        monkeypatch, staff_api_client, category, permission_manage_products):
    query = """
        mutation($id: ID!, $name: String, $slug: String, $backgroundImage: Upload, $description: String) {
            categoryUpdate(
                id: $id
                input: {
                    name: $name
                    description: $description
                    backgroundImage: $backgroundImage
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

    mock_create_thumbnails = Mock(return_value=None)
    monkeypatch.setattr(
        ('saleor.dashboard.category.forms.'
         'create_category_background_image_thumbnails.delay'),
        mock_create_thumbnails)

    # create child category and test that the update mutation won't change
    # it's parent
    child_category = category.children.create(name='child')

    category_name = 'Updated name'
    category_slug = slugify(category_name)
    category_description = 'Updated description'
    image_file, image_name = create_image()

    category_id = graphene.Node.to_global_id('Category', child_category.pk)
    variables = {
        'name': category_name, 'description': category_description,
        'backgroundImage': image_name, 'id': category_id,
        'slug': category_slug}
    body = get_multipart_request_body(query, variables, image_file, image_name)
    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    data = content['data']['categoryUpdate']
    assert data['errors'] == []
    assert data['category']['id'] == category_id
    assert data['category']['name'] == category_name
    assert data['category']['description'] == category_description

    parent_id = graphene.Node.to_global_id('Category', category.pk)
    assert data['category']['parent']['id'] == parent_id
    category = Category.objects.get(name=category_name)
    assert category.background_image.file
    mock_create_thumbnails.assert_called_once_with(category.pk)


def test_category_update_mutation_without_background_image(
        monkeypatch, staff_api_client, category, permission_manage_products):
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

    mock_create_thumbnails = Mock(return_value=None)
    monkeypatch.setattr(
        ('saleor.dashboard.category.forms.'
         'create_category_background_image_thumbnails.delay'),
        mock_create_thumbnails)

    # create child category and test that the update mutation won't change
    # it's parent
    child_category = category.children.create(name='child')

    category_name = 'Updated name'
    category_slug = slugify(category_name)
    category_description = 'Updated description'

    category_id = graphene.Node.to_global_id('Category', child_category.pk)

    # test creating root category
    variables = {
        'id': category_id,
        'name': category_name, 'description': category_description,
        'slug': category_slug}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])

    content = get_graphql_content(response)
    data = content['data']['categoryUpdate']
    assert data['errors'] == []
    assert mock_create_thumbnails.call_count == 0


def test_category_delete_mutation(
        staff_api_client, category, permission_manage_products):
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
    variables = {'id': graphene.Node.to_global_id('Category', category.id)}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    data = content['data']['categoryDelete']
    assert data['category']['name'] == category.name
    with pytest.raises(category._meta.model.DoesNotExist):
        category.refresh_from_db()


def test_category_level(user_api_client, category):
    query = LEVELED_CATEGORIES_QUERY
    child = Category.objects.create(
        name='child', slug='chi-ld', parent=category)
    variables = {'level': 0}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    category_data = content['data']['categories']['edges'][0]['node']
    assert category_data['name'] == category.name
    assert category_data['parent'] is None

    variables = {'level': 1}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    category_data = content['data']['categories']['edges'][0]['node']
    assert category_data['name'] == child.name
    assert category_data['parent']['name'] == category.name


def test_category_image_query(user_api_client, non_default_category):
    category = non_default_category
    image_file, image_name = create_image()
    category.background_image = image_file
    category.save()
    category_id = graphene.Node.to_global_id('Category', category.pk)
    variables = {'id': category_id}
    response = user_api_client.post_graphql(FETCH_CATEGORY_QUERY, variables)
    content = get_graphql_content(response)
    data = content['data']['category']
    thumbnail_url = category.background_image.thumbnail['120x120'].url
    assert thumbnail_url in data['backgroundImage']['url']


def test_category_image_query_without_associated_file(
        user_api_client, non_default_category):
    category = non_default_category
    category_id = graphene.Node.to_global_id('Category', category.pk)
    variables = {'id': category_id}
    response = user_api_client.post_graphql(FETCH_CATEGORY_QUERY, variables)
    content = get_graphql_content(response)
    data = content['data']['category']
    assert data['name'] == category.name
    assert data['backgroundImage'] is None
