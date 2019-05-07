import json
from datetime import date
from unittest.mock import Mock

import graphene
import pytest
from django.utils.text import slugify
from graphql_relay import to_global_id

from saleor.product.models import Collection
from tests.utils import create_image, create_pdf_file_with_image_ext

from .utils import get_graphql_content, get_multipart_request_body


def test_collections_query(
        user_api_client, staff_api_client, collection, draft_collection,
        permission_manage_products):
    query = """
        query Collections {
            collections(first: 2) {
                edges {
                    node {
                        isPublished
                        name
                        slug
                        description
                        products {
                            totalCount
                        }
                    }
                }
            }
        }
    """

    # query public collections only as regular user
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    edges = content['data']['collections']['edges']
    assert len(edges) == 1
    collection_data = edges[0]['node']
    assert collection_data['isPublished']
    assert collection_data['name'] == collection.name
    assert collection_data['slug'] == collection.slug
    assert collection_data['description'] == collection.description
    assert collection_data['products'][
               'totalCount'] == collection.products.count()

    # query all collections only as a staff user with proper permissions
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query)
    content = get_graphql_content(response)
    edges = content['data']['collections']['edges']
    assert len(edges) == 2


def test_create_collection(
        monkeypatch, staff_api_client, product_list, media_root,
        permission_manage_products):
    query = """
        mutation createCollection(
                $name: String!, $slug: String!, $description: String,
                $descriptionJson: JSONString, $products: [ID],
                $backgroundImage: Upload!, $backgroundImageAlt: String,
                $isPublished: Boolean!, $publicationDate: Date) {
            collectionCreate(
                input: {
                    name: $name,
                    slug: $slug,
                    description: $description,
                    descriptionJson: $descriptionJson,
                    products: $products,
                    backgroundImage: $backgroundImage,
                    backgroundImageAlt: $backgroundImageAlt,
                    isPublished: $isPublished,
                    publicationDate: $publicationDate}) {
                collection {
                    name
                    slug
                    description
                    descriptionJson
                    products {
                        totalCount
                    }
                    publicationDate
                    backgroundImage{
                        alt
                    }
                }
            }
        }
    """

    mock_create_thumbnails = Mock(return_value=None)
    monkeypatch.setattr(
        ('saleor.dashboard.collection.forms.'
         'create_collection_background_image_thumbnails.delay'),
        mock_create_thumbnails)

    product_ids = [
        to_global_id('Product', product.pk) for product in product_list]
    image_file, image_name = create_image()
    image_alt = 'Alt text for an image.'
    name = 'test-name'
    slug = 'test-slug'
    description = 'test-description'
    description_json = json.dumps({'content': 'description'})
    publication_date = date.today()
    variables = {
        'name': name, 'slug': slug, 'description': description,
        'descriptionJson': description_json, 'products': product_ids,
        'backgroundImage': image_name, 'backgroundImageAlt': image_alt,
        'isPublished': True, 'publicationDate': publication_date}
    body = get_multipart_request_body(query, variables, image_file, image_name)
    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    data = content['data']['collectionCreate']['collection']
    assert data['name'] == name
    assert data['slug'] == slug
    assert data['description'] == description
    assert data['descriptionJson'] == description_json
    assert data['publicationDate'] == publication_date.isoformat()
    assert data['products']['totalCount'] == len(product_ids)
    collection = Collection.objects.get(slug=slug)
    assert collection.background_image.file
    mock_create_thumbnails.assert_called_once_with(collection.pk)
    assert data['backgroundImage']['alt'] == image_alt


def test_create_collection_without_background_image(
        monkeypatch, staff_api_client, product_list,
        permission_manage_products):
    query = """
        mutation createCollection(
            $name: String!, $slug: String!, $products: [ID], $isPublished: Boolean!) {
            collectionCreate(
                input: {name: $name, slug: $slug, products: $products, isPublished: $isPublished}) {
                errors {
                    field
                    message
                }
            }
        }
    """

    mock_create_thumbnails = Mock(return_value=None)
    monkeypatch.setattr(
        ('saleor.dashboard.collection.forms.'
         'create_collection_background_image_thumbnails.delay'),
        mock_create_thumbnails)

    variables = {
        'name': 'test-name', 'slug': 'test-slug', 'isPublished': True, }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    get_graphql_content(response)
    assert mock_create_thumbnails.call_count == 0


def test_update_collection(
        monkeypatch, staff_api_client, collection, permission_manage_products):
    query = """
        mutation updateCollection(
            $name: String!, $slug: String!, $description: String, $id: ID!, $isPublished: Boolean!, $publicationDate: Date) {
            collectionUpdate(
                id: $id, input: {name: $name, slug: $slug, description: $description, isPublished: $isPublished, publicationDate: $publicationDate}) {
                collection {
                    name
                    slug
                    description
                    publicationDate
                }
            }
        }
    """

    mock_create_thumbnails = Mock(return_value=None)
    monkeypatch.setattr(
        ('saleor.dashboard.collection.forms.'
         'create_collection_background_image_thumbnails.delay'),
        mock_create_thumbnails)

    name = 'new-name'
    slug = 'new-slug'
    description = 'new-description'
    publication_date = date.today()
    variables = {
        'name': name, 'slug': slug, 'description': description,
        'id': to_global_id('Collection', collection.id), 'isPublished': True,
        'publicationDate': publication_date}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    data = content['data']['collectionUpdate']['collection']
    assert data['name'] == name
    assert data['slug'] == slug
    assert data['publicationDate'] == publication_date.isoformat()
    assert mock_create_thumbnails.call_count == 0


MUTATION_UPDATE_COLLECTION_WITH_BACKGROUND_IMAGE = """
    mutation updateCollection($name: String!, $slug: String!, $id: ID!, $backgroundImage: Upload, $backgroundImageAlt: String, $isPublished: Boolean!) {
        collectionUpdate(
            id: $id, input: {
                name: $name,
                slug: $slug,
                backgroundImage: $backgroundImage,
                backgroundImageAlt: $backgroundImageAlt,
                isPublished: $isPublished
            }
        ) {
            collection {
                slug
                backgroundImage{
                    alt
                }
            }
            errors {
                field
                message
            }
        }
    }"""


def test_update_collection_with_background_image(
        monkeypatch, staff_api_client, collection, permission_manage_products,
        media_root):
    mock_create_thumbnails = Mock(return_value=None)
    monkeypatch.setattr(
        ('saleor.dashboard.collection.forms.'
         'create_collection_background_image_thumbnails.delay'),
        mock_create_thumbnails)

    image_file, image_name = create_image()
    image_alt = 'Alt text for an image.'
    variables = {
        'name': 'new-name',
        'slug': 'new-slug',
        'id': to_global_id('Collection', collection.id),
        'backgroundImage': image_name,
        'backgroundImageAlt': image_alt,
        'isPublished': True}
    body = get_multipart_request_body(
        MUTATION_UPDATE_COLLECTION_WITH_BACKGROUND_IMAGE, variables,
        image_file, image_name)
    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    data = content['data']['collectionUpdate']
    assert not data['errors']
    slug = data['collection']['slug']
    collection = Collection.objects.get(slug=slug)
    assert collection.background_image
    mock_create_thumbnails.assert_called_once_with(collection.pk)
    assert data['collection']['backgroundImage']['alt'] == image_alt


def test_update_collection_invalid_background_image(
        staff_api_client, collection, permission_manage_products):
    image_file, image_name = create_pdf_file_with_image_ext()
    image_alt = 'Alt text for an image.'
    variables = {
        'name': 'new-name',
        'slug': 'new-slug',
        'id': to_global_id('Collection', collection.id),
        'backgroundImage': image_name,
        'backgroundImageAlt': image_alt,
        'isPublished': True}
    body = get_multipart_request_body(
        MUTATION_UPDATE_COLLECTION_WITH_BACKGROUND_IMAGE, variables,
        image_file, image_name)
    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    data = content['data']['collectionUpdate']
    assert data['errors'][0]['field'] == 'backgroundImage'
    assert data['errors'][0]['message'] == 'Invalid file type'


def test_delete_collection(
        staff_api_client, collection, permission_manage_products):
    query = """
        mutation deleteCollection($id: ID!) {
            collectionDelete(id: $id) {
                collection {
                    name
                }
            }
        }
    """
    collection_id = to_global_id('Collection', collection.id)
    variables = {'id': collection_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    data = content['data']['collectionDelete']['collection']
    assert data['name'] == collection.name
    with pytest.raises(collection._meta.model.DoesNotExist):
        collection.refresh_from_db()


def test_auto_create_slug_on_collection(
        staff_api_client, product_list, permission_manage_products):
    query = """
        mutation createCollection(
            $name: String!, $isPublished: Boolean!) {
            collectionCreate(
                input: {name: $name, isPublished: $isPublished}) {
                collection {
                    name
                    slug
                }
            }
        }
    """
    name = 'test name123'
    variables = {'name': name, 'isPublished': True}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    data = content['data']['collectionCreate']['collection']
    assert data['name'] == name
    assert data['slug'] == slugify(name)


def test_add_products_to_collection(
        staff_api_client, collection, product_list,
        permission_manage_products):
    query = """
        mutation collectionAddProducts(
            $id: ID!, $products: [ID]!) {
            collectionAddProducts(collectionId: $id, products: $products) {
                collection {
                    products {
                        totalCount
                    }
                }
            }
        }
    """
    collection_id = to_global_id('Collection', collection.id)
    product_ids = [
        to_global_id('Product', product.pk) for product in product_list]
    no_products_before = collection.products.count()
    variables = {'id': collection_id, 'products': product_ids}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    data = content['data']['collectionAddProducts']['collection']
    assert data[
               'products']['totalCount'] == no_products_before + len(
        product_ids)


def test_remove_products_from_collection(
        staff_api_client, collection, product_list,
        permission_manage_products):
    query = """
        mutation collectionRemoveProducts(
            $id: ID!, $products: [ID]!) {
            collectionRemoveProducts(collectionId: $id, products: $products) {
                collection {
                    products {
                        totalCount
                    }
                }
            }
        }
    """
    collection.products.add(*product_list)
    collection_id = to_global_id('Collection', collection.id)
    product_ids = [
        to_global_id('Product', product.pk) for product in product_list]
    no_products_before = collection.products.count()
    variables = {'id': collection_id, 'products': product_ids}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    data = content['data']['collectionRemoveProducts']['collection']
    assert data[
               'products']['totalCount'] == no_products_before - len(
        product_ids)


FETCH_COLLECTION_QUERY = """
    query fetchCollection($id: ID!){
        collection(id: $id) {
            name
            backgroundImage(size: 120) {
               url
               alt
            }
        }
    }
"""


def test_collection_image_query(user_api_client, collection, media_root):
    alt_text = 'Alt text for an image.'
    image_file, image_name = create_image()
    collection.background_image = image_file
    collection.background_image_alt = alt_text
    collection.save()
    collection_id = graphene.Node.to_global_id('Collection', collection.pk)
    variables = {'id': collection_id}
    response = user_api_client.post_graphql(FETCH_COLLECTION_QUERY, variables)
    content = get_graphql_content(response)
    data = content['data']['collection']
    thumbnail_url = collection.background_image.thumbnail['120x120'].url
    assert thumbnail_url in data['backgroundImage']['url']
    assert data['backgroundImage']['alt'] == alt_text


def test_collection_image_query_without_associated_file(
        user_api_client, collection):
    collection_id = graphene.Node.to_global_id('Collection', collection.pk)
    variables = {'id': collection_id}
    response = user_api_client.post_graphql(FETCH_COLLECTION_QUERY, variables)
    content = get_graphql_content(response)
    data = content['data']['collection']
    assert data['name'] == collection.name
    assert data['backgroundImage'] is None


def test_update_collection_mutation_remove_background_image(
        staff_api_client, collection_with_image, permission_manage_products):
    query = """
        mutation updateCollection($id: ID!, $backgroundImage: Upload) {
            collectionUpdate(
                id: $id, input: {
                    backgroundImage: $backgroundImage
                }
            ) {
                collection {
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
    assert collection_with_image.background_image
    variables = {
        'id': to_global_id('Collection', collection_with_image.id),
        'backgroundImage': None}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    data = content['data']['collectionUpdate']['collection']
    assert not data['backgroundImage']
    collection_with_image.refresh_from_db()
    assert not collection_with_image.background_image


def _fetch_collection(client, collection, permissions=None):
    query = """
    query fetchCollection($collectionId: ID!){
        collection(id: $collectionId) {
            name,
            isPublished
        }
    }
    """
    variables = {
        'collectionId': graphene.Node.to_global_id(
            'Collection', collection.id)}
    response = client.post_graphql(
        query, variables, permissions=permissions, check_no_permissions=False)
    content = get_graphql_content(response)
    return content['data']['collection']


def test_fetch_unpublished_collection_staff_user(
        staff_api_client, unpublished_collection, permission_manage_products):
    collection_data = _fetch_collection(
        staff_api_client,
        unpublished_collection,
        permissions=[permission_manage_products])
    assert collection_data['name'] == unpublished_collection.name
    assert collection_data[
               'isPublished'] == unpublished_collection.is_published


def test_fetch_unpublished_collection_customer(
        user_api_client, unpublished_collection):
    collection_data = _fetch_collection(
        user_api_client, unpublished_collection)
    assert collection_data is None


def test_fetch_unpublished_collection_anonymous_user(
        api_client, unpublished_collection):
    collection_data = _fetch_collection(api_client, unpublished_collection)
    assert collection_data is None


MUTATION_BULK_PUBLISH_COLLECTIONS = """
        mutation publishManyCollections($ids: [ID]!, $is_published: Boolean!) {
            collectionBulkPublish(ids: $ids, isPublished: $is_published) {
                count
            }
        }
    """


def test_bulk_publish_collection(
        staff_api_client, collection_list_unpublished,
        permission_manage_products):
    collection_list = collection_list_unpublished
    assert not any(collection.is_published for collection in collection_list)

    variables = {'ids': [
        graphene.Node.to_global_id('Collection', collection.id)
        for collection in collection_list], 'is_published': True}
    response = staff_api_client.post_graphql(
        MUTATION_BULK_PUBLISH_COLLECTIONS, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    collection_list = Collection.objects.filter(
        id__in=[collection.pk for collection in collection_list])

    assert content['data']['collectionBulkPublish']['count'] == len(
        collection_list)
    assert all(collection.is_published for collection in collection_list)


def test_bulk_unpublish_collection(
        staff_api_client, collection_list,
        permission_manage_products):
    assert all(collection.is_published for collection in collection_list)

    variables = {'ids': [
        graphene.Node.to_global_id('Collection', collection.id)
        for collection in collection_list], 'is_published': False}
    response = staff_api_client.post_graphql(
        MUTATION_BULK_PUBLISH_COLLECTIONS, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    collection_list = Collection.objects.filter(
        id__in=[collection.pk for collection in collection_list])

    assert content['data']['collectionBulkPublish']['count'] == len(
        collection_list)
    assert not any(collection.is_published for collection in collection_list)
