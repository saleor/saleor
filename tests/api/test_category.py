import json
from unittest.mock import Mock

import graphene
import pytest
from django.template.defaultfilters import slugify
from graphql_relay import to_global_id

from saleor.product.models import Category
from tests.api.utils import get_graphql_content, get_multipart_request_body
from tests.utils import create_image, create_pdf_file_with_image_ext


def test_category_query(user_api_client, product):
    category = Category.objects.first()
    query = """
    query {
        category(id: "%(category_pk)s") {
            id
            name
            ancestors(last: 20) {
                edges {
                    node {
                        name
                    }
                }
            }
            children(first: 20) {
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
        monkeypatch, staff_api_client, permission_manage_products, media_root):
    query = """
        mutation(
                $name: String, $slug: String, $description: String,
                $descriptionJson: JSONString, $backgroundImage: Upload,
                $backgroundImageAlt: String, $parentId: ID) {
            categoryCreate(
                input: {
                    name: $name
                    slug: $slug
                    description: $description
                    descriptionJson: $descriptionJson
                    backgroundImage: $backgroundImage
                    backgroundImageAlt: $backgroundImageAlt
                },
                parent: $parentId
            ) {
                category {
                    id
                    name
                    slug
                    description
                    descriptionJson
                    parent {
                        name
                        id
                    }
                    backgroundImage{
                        alt
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
    category_description_json = json.dumps({'content': 'description'})
    image_file, image_name = create_image()
    image_alt = 'Alt text for an image.'

    # test creating root category
    variables = {
        'name': category_name, 'description': category_description,
        'descriptionJson': category_description_json,
        'backgroundImage': image_name, 'backgroundImageAlt': image_alt,
        'slug': category_slug}
    body = get_multipart_request_body(query, variables, image_file, image_name)
    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    data = content['data']['categoryCreate']
    assert data['errors'] == []
    assert data['category']['name'] == category_name
    assert data['category']['description'] == category_description
    assert data['category']['descriptionJson'] == category_description_json
    assert not data['category']['parent']
    category = Category.objects.get(name=category_name)
    assert category.background_image.file
    mock_create_thumbnails.assert_called_once_with(category.pk)
    assert data['category']['backgroundImage']['alt'] == image_alt

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

    # test creating root category
    category_name = 'Test category'
    variables = {
        'name': category_name,
        'description': 'Test description',
        'slug': slugify(category_name)}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    data = content['data']['categoryCreate']
    assert data['errors'] == []
    assert mock_create_thumbnails.call_count == 0


MUTATION_CATEGORY_UPDATE_MUTATION = """
    mutation($id: ID!, $name: String, $slug: String, $backgroundImage: Upload, $backgroundImageAlt: String, $description: String) {
        categoryUpdate(
            id: $id
            input: {
                name: $name
                description: $description
                backgroundImage: $backgroundImage
                backgroundImageAlt: $backgroundImageAlt
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
                backgroundImage{
                    alt
                }
            }
            errors {
                field
                message
            }
        }
    }
    """


def test_category_update_mutation(
        monkeypatch, staff_api_client, category, permission_manage_products,
        media_root):
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
    image_alt = 'Alt text for an image.'

    category_id = graphene.Node.to_global_id('Category', child_category.pk)
    variables = {
        'name': category_name, 'description': category_description,
        'backgroundImage': image_name, 'backgroundImageAlt': image_alt,
        'id': category_id, 'slug': category_slug}
    body = get_multipart_request_body(
        MUTATION_CATEGORY_UPDATE_MUTATION, variables, image_file, image_name)
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
    assert data['category']['backgroundImage']['alt'] == image_alt


def test_category_update_mutation_invalid_background_image(
        staff_api_client, category, permission_manage_products):
    image_file, image_name = create_pdf_file_with_image_ext()
    image_alt = 'Alt text for an image.'
    variables = {
        'name': 'new-name',
        'slug': 'new-slug',
        'id': to_global_id('Category', category.id),
        'backgroundImage': image_name,
        'backgroundImageAlt': image_alt,
        'isPublished': True}
    body = get_multipart_request_body(
        MUTATION_CATEGORY_UPDATE_MUTATION, variables,
        image_file, image_name)
    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    data = content['data']['categoryUpdate']
    assert data['errors'][0]['field'] == 'backgroundImage'
    assert data['errors'][0]['message'] == 'Invalid file type'


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

    category_name = 'Updated name'
    variables = {
        'id': graphene.Node.to_global_id(
            'Category', category.children.create(name='child').pk),
        'name': category_name,
        'description': 'Updated description',
        'slug': slugify(category_name)}
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


LEVELED_CATEGORIES_QUERY = """
    query leveled_categories($level: Int) {
        categories(level: $level, first: 20) {
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


FETCH_CATEGORY_QUERY = """
    query fetchCategory($id: ID!){
        category(id: $id) {
            name
            backgroundImage(size: 120) {
            url
            alt
            }
        }
    }
    """


def test_category_image_query(
        user_api_client, non_default_category, media_root):
    alt_text = 'Alt text for an image.'
    category = non_default_category
    image_file, image_name = create_image()
    category.background_image = image_file
    category.background_image_alt = alt_text
    category.save()
    category_id = graphene.Node.to_global_id('Category', category.pk)
    variables = {'id': category_id}
    response = user_api_client.post_graphql(FETCH_CATEGORY_QUERY, variables)
    content = get_graphql_content(response)
    data = content['data']['category']
    thumbnail_url = category.background_image.thumbnail['120x120'].url
    assert thumbnail_url in data['backgroundImage']['url']
    assert data['backgroundImage']['alt'] == alt_text


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


def test_update_category_mutation_remove_background_image(
        staff_api_client, category_with_image, permission_manage_products):
    query = """
        mutation updateCategory($id: ID!, $backgroundImage: Upload) {
            categoryUpdate(
                id: $id, input: {
                    backgroundImage: $backgroundImage
                }
            ) {
                category {
                    backgroundImage{
                        url
                    }
                }
                errors {
                    field
                    message
                }
            }
        }
    """
    assert category_with_image.background_image
    variables = {
        'id': to_global_id('Category', category_with_image.id),
        'backgroundImage': None}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    data = content['data']['categoryUpdate']['category']
    assert not data['backgroundImage']
    category_with_image.refresh_from_db()
    assert not category_with_image.background_image
