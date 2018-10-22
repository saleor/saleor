import pytest

import graphene
from django.template.defaultfilters import slugify
from saleor.product.models import Category
from tests.utils import create_image
from tests.api.utils import get_graphql_content, get_multipart_request_body


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
        staff_api_client, permission_manage_products):
    query = """
        mutation($name: String, $slug: String, $description: String, $backgroundImage: Upload, $parentId: ID) {
            categoryCreate(
                input: {
                    name: $name
                    slug: $slug
                    description: $description
                    backgroundImage: $backgroundImage
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


def test_category_update_mutation(
        staff_api_client, category, permission_manage_products):
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
    variables = {'level': 0}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
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
    variables = {'level': 1}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    category_data = content['data']['categories']['edges'][0]['node']
    assert category_data['name'] == child.name
    assert category_data['parent']['name'] == category.name
