import os
from unittest.mock import MagicMock, patch

import graphene
import pytest
from django.core.files import File
from graphql_relay import to_global_id

from ....product.error_codes import CollectionErrorCode, ProductErrorCode
from ....product.models import Collection, Product
from ....product.tests.utils import create_image, create_pdf_file_with_image_ext
from ....tests.consts import TEST_SERVER_DOMAIN
from ....tests.utils import dummy_editorjs
from ....thumbnail.models import Thumbnail
from ...core.enums import ThumbnailFormatEnum
from ...tests.utils import (
    get_graphql_content,
    get_graphql_content_from_response,
    get_multipart_request_body,
)

QUERY_COLLECTION = """
    query ($id: ID, $slug: String, $channel: String){
        collection(
            id: $id,
            slug: $slug,
            channel: $channel,
        ) {
            id
            name
        }
    }
    """


def test_collection_query_by_id(user_api_client, published_collection, channel_USD):
    variables = {
        "id": graphene.Node.to_global_id("Collection", published_collection.pk),
        "channel": channel_USD.slug,
    }

    response = user_api_client.post_graphql(QUERY_COLLECTION, variables=variables)
    content = get_graphql_content(response)
    collection_data = content["data"]["collection"]
    assert collection_data is not None
    assert collection_data["name"] == published_collection.name


def test_collection_query_unpublished_collection_by_id_as_app(
    app_api_client, unpublished_collection, permission_manage_products, channel_USD
):
    # given
    variables = {
        "id": graphene.Node.to_global_id("Collection", unpublished_collection.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = app_api_client.post_graphql(
        QUERY_COLLECTION,
        variables=variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    collection_data = content["data"]["collection"]
    assert collection_data is not None
    assert collection_data["name"] == unpublished_collection.name


def test_collection_query_by_slug(user_api_client, published_collection, channel_USD):
    variables = {
        "slug": published_collection.slug,
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(QUERY_COLLECTION, variables=variables)
    content = get_graphql_content(response)
    collection_data = content["data"]["collection"]
    assert collection_data is not None
    assert collection_data["name"] == published_collection.name


def test_collection_query_unpublished_collection_by_slug_as_staff(
    staff_api_client, unpublished_collection, permission_manage_products, channel_USD
):
    # given
    user = staff_api_client.user
    user.user_permissions.add(permission_manage_products)

    variables = {"slug": unpublished_collection.slug, "channel": channel_USD.slug}

    # when
    response = staff_api_client.post_graphql(QUERY_COLLECTION, variables=variables)

    # then
    content = get_graphql_content(response)
    collection_data = content["data"]["collection"]
    assert collection_data is not None
    assert collection_data["name"] == unpublished_collection.name


def test_collection_query_unpublished_collection_by_slug_and_anonymous_user(
    api_client, unpublished_collection, channel_USD
):
    # given
    variables = {"slug": unpublished_collection.slug, "channel": channel_USD.slug}

    # when
    response = api_client.post_graphql(QUERY_COLLECTION, variables=variables)

    # then
    content = get_graphql_content(response)
    collection_data = content["data"]["collection"]
    assert collection_data is None


def test_collection_query_error_when_id_and_slug_provided(
    user_api_client,
    collection,
    graphql_log_handler,
):
    variables = {
        "id": graphene.Node.to_global_id("Collection", collection.pk),
        "slug": collection.slug,
    }
    response = user_api_client.post_graphql(QUERY_COLLECTION, variables=variables)
    assert graphql_log_handler.messages == [
        "saleor.graphql.errors.handled[INFO].GraphQLError"
    ]
    content = get_graphql_content(response, ignore_errors=True)
    assert len(content["errors"]) == 1


def test_collection_query_error_when_no_param(
    user_api_client,
    collection,
    graphql_log_handler,
):
    variables = {}
    response = user_api_client.post_graphql(QUERY_COLLECTION, variables=variables)
    assert graphql_log_handler.messages == [
        "saleor.graphql.errors.handled[INFO].GraphQLError"
    ]
    content = get_graphql_content(response, ignore_errors=True)
    assert len(content["errors"]) == 1


def test_collections_query(
    user_api_client,
    published_collection,
    unpublished_collection,
    permission_manage_products,
    channel_USD,
):
    query = """
        query Collections ($channel: String) {
            collections(first:2, channel: $channel) {
                edges {
                    node {
                        name
                        slug
                        description
                        descriptionJson
                        products {
                            totalCount
                        }
                    }
                }
            }
        }
    """

    # query public collections only as regular user
    variables = {"channel": channel_USD.slug}
    description = dummy_editorjs("Test description.", json_format=True)
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    edges = content["data"]["collections"]["edges"]
    assert len(edges) == 1
    collection_data = edges[0]["node"]
    assert collection_data["name"] == published_collection.name
    assert collection_data["slug"] == published_collection.slug
    assert collection_data["description"] == description
    assert collection_data["descriptionJson"] == description
    assert (
        collection_data["products"]["totalCount"]
        == published_collection.products.count()
    )


def test_collections_query_without_description(
    user_api_client,
    published_collection,
    unpublished_collection,
    permission_manage_products,
    channel_USD,
):
    query = """
        query Collections ($channel: String) {
            collections(first:2, channel: $channel) {
                edges {
                    node {
                        name
                        slug
                        description
                        descriptionJson
                    }
                }
            }
        }
    """

    # query public collections only as regular user
    variables = {"channel": channel_USD.slug}
    collection = published_collection
    collection.description = None
    collection.save()
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    edges = content["data"]["collections"]["edges"]
    assert len(edges) == 1
    collection_data = edges[0]["node"]
    assert collection_data["name"] == collection.name
    assert collection_data["slug"] == collection.slug
    assert collection_data["description"] is None
    assert collection_data["descriptionJson"] == "{}"


def test_collections_query_as_staff(
    staff_api_client,
    published_collection,
    unpublished_collection_PLN,
    permission_manage_products,
    channel_USD,
):
    query = """
        query Collections($channel: String) {
            collections(first: 2, channel: $channel) {
                edges {
                    node {
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
    # query all collections only as a staff user with proper permissions
    variables = {"channel": channel_USD.slug}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    edges = content["data"]["collections"]["edges"]
    assert len(edges) == 1


def test_collections_query_as_staff_without_channel(
    staff_api_client,
    published_collection,
    unpublished_collection_PLN,
    permission_manage_products,
    channel_USD,
):
    query = """
        query Collections($channel: String) {
            collections(first: 2, channel: $channel) {
                edges {
                    node {
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
    # query all collections only as a staff user with proper permissions
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query)
    content = get_graphql_content(response)
    edges = content["data"]["collections"]["edges"]
    assert len(edges) == 2


GET_FILTERED_PRODUCTS_COLLECTION_QUERY = """
query CollectionProducts($id: ID!,$channel: String, $filters: ProductFilterInput) {
  collection(id: $id, channel: $channel) {
    products(first: 10, filter: $filters) {
      edges {
        node {
          id
          attributes {
            attribute {
              choices(first: 10) {
                edges {
                  node {
                    slug
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
"""


def test_filter_collection_products(
    user_api_client, product_list, published_collection, channel_USD, channel_PLN
):
    # given
    query = GET_FILTERED_PRODUCTS_COLLECTION_QUERY

    for product in product_list:
        published_collection.products.add(product)

    product = product_list[0]

    variables = {
        "id": graphene.Node.to_global_id("Collection", published_collection.pk),
        "filters": {"search": product.name},
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    product_data = content["data"]["collection"]["products"]["edges"][0]["node"]

    assert product_data["id"] == graphene.Node.to_global_id("Product", product.pk)


def test_filter_collection_published_products(
    user_api_client, product_list, published_collection, channel_USD, channel_PLN
):
    # given
    query = GET_FILTERED_PRODUCTS_COLLECTION_QUERY

    for product in product_list:
        published_collection.products.add(product)

    product = product_list[0]
    listing = product.channel_listings.first()
    listing.is_published = False
    listing.save(update_fields=["is_published"])

    product_id = graphene.Node.to_global_id("Product", product.id)

    variables = {
        "id": graphene.Node.to_global_id("Collection", published_collection.pk),
        "filters": {"isPublished": True},
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    products = content["data"]["collection"]["products"]["edges"]

    assert len(products) == len(product_list) - 1
    assert product_id not in {node["node"]["id"] for node in products}


def test_filter_collection_products_by_multiple_attributes(
    user_api_client,
    published_collection,
    product_with_two_variants,
    product_with_multiple_values_attributes,
    channel_USD,
):
    # given
    published_collection.products.set(
        [product_with_two_variants, product_with_multiple_values_attributes]
    )
    assert published_collection.products.count() == 2

    filters = {
        "attributes": [{"slug": "modes", "values": ["eco"]}],
    }
    variables = {
        "id": graphene.Node.to_global_id("Collection", published_collection.pk),
        "filters": filters,
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(
        GET_FILTERED_PRODUCTS_COLLECTION_QUERY, variables
    )

    # then
    content = get_graphql_content(response)
    products_data = content["data"]["collection"]["products"]["edges"]
    product = products_data[0]["node"]

    _, _id = graphene.Node.from_global_id(product["id"])

    assert len(products_data) == 1
    assert product["id"] == graphene.Node.to_global_id(
        "Product", product_with_multiple_values_attributes.pk
    )
    assert product["attributes"] == [
        {
            "attribute": {
                "choices": {
                    "edges": [
                        {"node": {"slug": "eco"}},
                        {"node": {"slug": "power"}},
                    ]
                }
            }
        }
    ]


CREATE_COLLECTION_MUTATION = """
        mutation createCollection(
                $name: String!, $slug: String,
                $description: JSONString, $products: [ID!],
                $backgroundImage: Upload, $backgroundImageAlt: String) {
            collectionCreate(
                input: {
                    name: $name,
                    slug: $slug,
                    description: $description,
                    products: $products,
                    backgroundImage: $backgroundImage,
                    backgroundImageAlt: $backgroundImageAlt}) {
                collection {
                    name
                    slug
                    description
                    products {
                        totalCount
                    }
                    backgroundImage{
                        alt
                    }
                }
                errors {
                    field
                    message
                    code
                }
            }
        }
"""


@patch("saleor.plugins.manager.PluginsManager.collection_updated")
@patch("saleor.plugins.manager.PluginsManager.collection_created")
def test_create_collection(
    created_webhook_mock,
    updated_webhook_mock,
    monkeypatch,
    staff_api_client,
    product_list,
    media_root,
    permission_manage_products,
):
    query = CREATE_COLLECTION_MUTATION

    product_ids = [to_global_id("Product", product.pk) for product in product_list]
    image_file, image_name = create_image()
    image_alt = "Alt text for an image."
    name = "test-name"
    slug = "test-slug"
    description = dummy_editorjs("description", True)
    variables = {
        "name": name,
        "slug": slug,
        "description": description,
        "products": product_ids,
        "backgroundImage": image_name,
        "backgroundImageAlt": image_alt,
    }
    body = get_multipart_request_body(query, variables, image_file, image_name)
    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["collectionCreate"]["collection"]
    assert data["name"] == name
    assert data["slug"] == slug
    assert data["description"] == description
    assert data["products"]["totalCount"] == len(product_ids)
    collection = Collection.objects.get(slug=slug)
    assert collection.background_image.file
    img_name, format = os.path.splitext(image_file._name)
    file_name = collection.background_image.name
    assert file_name != image_file._name
    assert file_name.startswith(f"collection-backgrounds/{img_name}")
    assert file_name.endswith(format)
    assert data["backgroundImage"]["alt"] == image_alt

    created_webhook_mock.assert_called_once()
    updated_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_create_collection_trigger_product_update_webhook(
    product_updated_mock,
    staff_api_client,
    product_list,
    media_root,
    permission_manage_products,
):
    query = CREATE_COLLECTION_MUTATION

    product_ids = [to_global_id("Product", product.pk) for product in product_list]
    name = "test-name"
    slug = "test-slug"
    description = dummy_editorjs("description", True)
    variables = {
        "name": name,
        "slug": slug,
        "description": description,
        "products": product_ids,
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["collectionCreate"]["collection"]

    assert data["name"] == name
    assert data["slug"] == slug
    assert data["description"] == description
    assert data["products"]["totalCount"] == len(product_ids)
    assert len(product_ids) == product_updated_mock.call_count


def test_create_collection_without_background_image(
    monkeypatch, staff_api_client, product_list, permission_manage_products
):
    query = CREATE_COLLECTION_MUTATION
    slug = "test-slug"

    variables = {"name": "test-name", "slug": slug}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["collectionCreate"]
    assert not data["errors"]
    assert data["collection"]["slug"] == slug


@pytest.mark.parametrize(
    "input_slug, expected_slug",
    (
        ("test-slug", "test-slug"),
        (None, "test-collection"),
        ("", "test-collection"),
        ("わたし-わ-にっぽん-です", "わたし-わ-にっぽん-です"),
    ),
)
def test_create_collection_with_given_slug(
    staff_api_client, permission_manage_products, input_slug, expected_slug, channel_USD
):
    query = CREATE_COLLECTION_MUTATION
    name = "Test collection"
    variables = {"name": name, "slug": input_slug}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["collectionCreate"]
    assert not data["errors"]
    assert data["collection"]["slug"] == expected_slug


def test_create_collection_name_with_unicode(
    staff_api_client, permission_manage_products, channel_USD
):
    query = CREATE_COLLECTION_MUTATION
    name = "わたし わ にっぽん です"
    variables = {"name": name}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["collectionCreate"]
    assert not data["errors"]
    assert data["collection"]["name"] == name
    assert data["collection"]["slug"] == "watasi-wa-nitupon-desu"


@patch("saleor.plugins.manager.PluginsManager.collection_updated")
@patch("saleor.plugins.manager.PluginsManager.collection_created")
def test_update_collection(
    created_webhook_mock,
    updated_webhook_mock,
    monkeypatch,
    staff_api_client,
    collection,
    permission_manage_products,
):
    query = """
        mutation updateCollection(
            $name: String!, $slug: String!, $description: JSONString, $id: ID!) {

            collectionUpdate(
                id: $id, input: {name: $name, slug: $slug, description: $description}) {

                collection {
                    name
                    slug
                    description
                }
            }
        }
    """
    description = dummy_editorjs("test description", True)

    name = "new-name"
    slug = "new-slug"
    description = description
    variables = {
        "name": name,
        "slug": slug,
        "description": description,
        "id": to_global_id("Collection", collection.id),
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["collectionUpdate"]["collection"]
    assert data["name"] == name
    assert data["slug"] == slug

    created_webhook_mock.assert_not_called()
    updated_webhook_mock.assert_called_once()


MUTATION_UPDATE_COLLECTION_WITH_BACKGROUND_IMAGE = """
    mutation updateCollection($name: String!, $slug: String!, $id: ID!,
            $backgroundImage: Upload, $backgroundImageAlt: String) {
        collectionUpdate(
            id: $id, input: {
                name: $name,
                slug: $slug,
                backgroundImage: $backgroundImage,
                backgroundImageAlt: $backgroundImageAlt,
            }
        ) {
            collection {
                slug
                backgroundImage{
                    alt
                    url
                }
            }
            errors {
                field
                message
            }
        }
    }"""


@patch("saleor.core.tasks.delete_from_storage_task.delay")
def test_update_collection_with_background_image(
    delete_from_storage_task_mock,
    staff_api_client,
    collection_with_image,
    permission_manage_products,
    media_root,
):
    # given
    image_file, image_name = create_image()
    image_alt = "Alt text for an image."

    collection = collection_with_image

    size = 128
    thumbnail_mock = MagicMock(spec=File)
    thumbnail_mock.name = "thumbnail_image.jpg"
    thumbnail = Thumbnail.objects.create(
        collection=collection, size=size, image=thumbnail_mock
    )
    img_path = thumbnail.image.name

    variables = {
        "name": "new-name",
        "slug": "new-slug",
        "id": to_global_id("Collection", collection.id),
        "backgroundImage": image_name,
        "backgroundImageAlt": image_alt,
    }
    body = get_multipart_request_body(
        MUTATION_UPDATE_COLLECTION_WITH_BACKGROUND_IMAGE,
        variables,
        image_file,
        image_name,
    )

    # when
    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["collectionUpdate"]
    assert not data["errors"]
    slug = data["collection"]["slug"]
    collection = Collection.objects.get(slug=slug)
    assert data["collection"]["backgroundImage"]["alt"] == image_alt
    assert data["collection"]["backgroundImage"]["url"].startswith(
        f"http://{TEST_SERVER_DOMAIN}/media/collection-backgrounds/{image_name}"
    )

    # ensure that thumbnails for old background image has been deleted
    assert not Thumbnail.objects.filter(collection_id=collection.id)
    delete_from_storage_task_mock.assert_called_once_with(img_path)


@patch("saleor.core.tasks.delete_from_storage_task.delay")
def test_update_collection_invalid_background_image(
    delete_from_storage_task_mock,
    staff_api_client,
    collection,
    permission_manage_products,
    media_root,
):
    # given
    image_file, image_name = create_pdf_file_with_image_ext()
    image_alt = "Alt text for an image."

    size = 128
    thumbnail_mock = MagicMock(spec=File)
    thumbnail_mock.name = "thumbnail_image.jpg"
    Thumbnail.objects.create(collection=collection, size=size, image=thumbnail_mock)

    variables = {
        "name": "new-name",
        "slug": "new-slug",
        "id": to_global_id("Collection", collection.id),
        "backgroundImage": image_name,
        "backgroundImageAlt": image_alt,
    }
    body = get_multipart_request_body(
        MUTATION_UPDATE_COLLECTION_WITH_BACKGROUND_IMAGE,
        variables,
        image_file,
        image_name,
    )

    # when
    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["collectionUpdate"]
    assert data["errors"][0]["field"] == "backgroundImage"
    assert data["errors"][0]["message"] == "Invalid file type."
    # ensure that thumbnails for old background image hasn't been deleted
    assert Thumbnail.objects.filter(collection_id=collection.id)
    delete_from_storage_task_mock.assert_not_called()


UPDATE_COLLECTION_SLUG_MUTATION = """
    mutation($id: ID!, $slug: String) {
        collectionUpdate(
            id: $id
            input: {
                slug: $slug
            }
        ) {
            collection{
                name
                slug
            }
            errors {
                field
                message
                code
            }
        }
    }
"""


@pytest.mark.parametrize(
    "input_slug, expected_slug, error_message",
    [
        ("test-slug", "test-slug", None),
        ("", "", "Slug value cannot be blank."),
        (None, "", "Slug value cannot be blank."),
    ],
)
def test_update_collection_slug(
    staff_api_client,
    collection,
    permission_manage_products,
    input_slug,
    expected_slug,
    error_message,
):
    query = UPDATE_COLLECTION_SLUG_MUTATION
    old_slug = collection.slug

    assert old_slug != input_slug

    node_id = graphene.Node.to_global_id("Collection", collection.id)
    variables = {"slug": input_slug, "id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["collectionUpdate"]
    errors = data["errors"]
    if not error_message:
        assert not errors
        assert data["collection"]["slug"] == expected_slug
    else:
        assert errors
        assert errors[0]["field"] == "slug"
        assert errors[0]["code"] == ProductErrorCode.REQUIRED.name


def test_update_collection_slug_exists(
    staff_api_client, collection, permission_manage_products
):
    query = UPDATE_COLLECTION_SLUG_MUTATION
    input_slug = "test-slug"

    second_collection = Collection.objects.get(pk=collection.pk)
    second_collection.pk = None
    second_collection.slug = input_slug
    second_collection.name = "Second collection"
    second_collection.save()

    assert input_slug != collection.slug

    node_id = graphene.Node.to_global_id("Collection", collection.id)
    variables = {"slug": input_slug, "id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["collectionUpdate"]
    errors = data["errors"]
    assert errors
    assert errors[0]["field"] == "slug"
    assert errors[0]["code"] == ProductErrorCode.UNIQUE.name


@pytest.mark.parametrize(
    "input_slug, expected_slug, input_name, error_message, error_field",
    [
        ("test-slug", "test-slug", "New name", None, None),
        ("", "", "New name", "Slug value cannot be blank.", "slug"),
        (None, "", "New name", "Slug value cannot be blank.", "slug"),
        ("test-slug", "", None, "This field cannot be blank.", "name"),
        ("test-slug", "", "", "This field cannot be blank.", "name"),
        (None, None, None, "Slug value cannot be blank.", "slug"),
    ],
)
def test_update_collection_slug_and_name(
    staff_api_client,
    collection,
    permission_manage_products,
    input_slug,
    expected_slug,
    input_name,
    error_message,
    error_field,
):
    query = """
            mutation($id: ID!, $name: String, $slug: String) {
            collectionUpdate(
                id: $id
                input: {
                    name: $name
                    slug: $slug
                }
            ) {
                collection{
                    name
                    slug
                }
                errors {
                    field
                    message
                    code
                }
            }
        }
    """

    old_name = collection.name
    old_slug = collection.slug

    assert input_slug != old_slug
    assert input_name != old_name

    node_id = graphene.Node.to_global_id("Collection", collection.id)
    variables = {"slug": input_slug, "name": input_name, "id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    collection.refresh_from_db()
    data = content["data"]["collectionUpdate"]
    errors = data["errors"]
    if not error_message:
        assert data["collection"]["name"] == input_name == collection.name
        assert data["collection"]["slug"] == input_slug == collection.slug
    else:
        assert errors
        assert errors[0]["field"] == error_field
        assert errors[0]["code"] == ProductErrorCode.REQUIRED.name


DELETE_COLLECTION_MUTATION = """
    mutation deleteCollection($id: ID!) {
        collectionDelete(id: $id) {
            collection {
                name
            }
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.collection_deleted")
def test_delete_collection(
    deleted_webhook_mock,
    staff_api_client,
    collection,
    permission_manage_products,
):
    # given
    query = DELETE_COLLECTION_MUTATION
    collection_id = to_global_id("Collection", collection.id)
    variables = {"id": collection_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["collectionDelete"]["collection"]
    assert data["name"] == collection.name
    with pytest.raises(collection._meta.model.DoesNotExist):
        collection.refresh_from_db()

    deleted_webhook_mock.assert_called_once()


@patch("saleor.core.tasks.delete_from_storage_task.delay")
def test_delete_collection_with_background_image(
    delete_from_storage_task_mock,
    staff_api_client,
    collection_with_image,
    permission_manage_products,
):
    # given
    query = DELETE_COLLECTION_MUTATION
    collection = collection_with_image

    thumbnail_mock = MagicMock(spec=File)
    thumbnail_mock.name = "thumbnail_image.jpg"
    Thumbnail.objects.create(collection=collection, size=128, image=thumbnail_mock)
    Thumbnail.objects.create(collection=collection, size=200, image=thumbnail_mock)

    collection_id = collection.id
    variables = {"id": to_global_id("Collection", collection.id)}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["collectionDelete"]["collection"]
    assert data["name"] == collection.name
    with pytest.raises(collection._meta.model.DoesNotExist):
        collection.refresh_from_db()
    # ensure all related thumbnails has been deleted
    assert not Thumbnail.objects.filter(collection_id=collection_id)
    assert delete_from_storage_task_mock.call_count == 3


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_delete_collection_trigger_product_updated_webhook(
    product_updated_mock,
    staff_api_client,
    collection,
    product_list,
    permission_manage_products,
):
    query = """
        mutation deleteCollection($id: ID!) {
            collectionDelete(id: $id) {
                collection {
                    name
                }
            }
        }
    """
    collection.products.add(*product_list)
    collection_id = to_global_id("Collection", collection.id)
    variables = {"id": collection_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["collectionDelete"]["collection"]
    assert data["name"] == collection.name
    with pytest.raises(collection._meta.model.DoesNotExist):
        collection.refresh_from_db()
    assert len(product_list) == product_updated_mock.call_count


def test_add_products_to_collection(
    staff_api_client, collection, product_list, permission_manage_products
):
    query = """
        mutation collectionAddProducts(
            $id: ID!, $products: [ID!]!) {
            collectionAddProducts(collectionId: $id, products: $products) {
                collection {
                    products {
                        totalCount
                    }
                }
            }
        }
    """
    collection_id = to_global_id("Collection", collection.id)
    product_ids = [to_global_id("Product", product.pk) for product in product_list]
    products_before = collection.products.count()
    variables = {"id": collection_id, "products": product_ids}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["collectionAddProducts"]["collection"]
    assert data["products"]["totalCount"] == products_before + len(product_ids)


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_add_products_to_collection_trigger_product_updated_webhook(
    product_updated_mock,
    staff_api_client,
    collection,
    product_list,
    permission_manage_products,
):
    query = """
        mutation collectionAddProducts(
            $id: ID!, $products: [ID!]!) {
            collectionAddProducts(collectionId: $id, products: $products) {
                collection {
                    products {
                        totalCount
                    }
                }
            }
        }
    """
    collection_id = to_global_id("Collection", collection.id)
    product_ids = [to_global_id("Product", product.pk) for product in product_list]
    products_before = collection.products.count()
    variables = {"id": collection_id, "products": product_ids}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["collectionAddProducts"]["collection"]
    assert data["products"]["totalCount"] == products_before + len(product_ids)
    assert len(product_list) == product_updated_mock.call_count


def test_add_products_to_collection_with_product_without_variants(
    staff_api_client, collection, product_list, permission_manage_products
):
    query = """
        mutation collectionAddProducts(
            $id: ID!, $products: [ID!]!) {
            collectionAddProducts(collectionId: $id, products: $products) {
                collection {
                    products {
                        totalCount
                    }
                }
                errors {
                    field
                    message
                    code
                }
            }
        }
    """
    product_list[0].variants.all().delete()
    collection_id = to_global_id("Collection", collection.id)
    product_ids = [to_global_id("Product", product.pk) for product in product_list]
    variables = {"id": collection_id, "products": product_ids}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    error = content["data"]["collectionAddProducts"]["errors"][0]

    assert (
        error["code"] == CollectionErrorCode.CANNOT_MANAGE_PRODUCT_WITHOUT_VARIANT.name
    )
    assert error["message"] == "Cannot manage products without variants."


def test_remove_products_from_collection(
    staff_api_client, collection, product_list, permission_manage_products
):
    query = """
        mutation collectionRemoveProducts(
            $id: ID!, $products: [ID!]!) {
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
    collection_id = to_global_id("Collection", collection.id)
    product_ids = [to_global_id("Product", product.pk) for product in product_list]
    products_before = collection.products.count()
    variables = {"id": collection_id, "products": product_ids}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["collectionRemoveProducts"]["collection"]
    assert data["products"]["totalCount"] == products_before - len(product_ids)


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_remove_products_from_collection_trigger_product_updated_webhook(
    product_updated_mock,
    staff_api_client,
    collection,
    product_list,
    permission_manage_products,
):
    query = """
        mutation collectionRemoveProducts(
            $id: ID!, $products: [ID!]!) {
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
    collection_id = to_global_id("Collection", collection.id)
    product_ids = [to_global_id("Product", product.pk) for product in product_list]
    products_before = collection.products.count()
    variables = {"id": collection_id, "products": product_ids}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["collectionRemoveProducts"]["collection"]
    assert data["products"]["totalCount"] == products_before - len(product_ids)
    assert len(product_list) == product_updated_mock.call_count


NOT_EXISTS_IDS_COLLECTIONS_QUERY = """
    query ($filter: CollectionFilterInput!, $channel: String) {
        collections(first: 5, filter: $filter, channel: $channel) {
            edges {
                node {
                    id
                    name
                }
            }
        }
    }
"""


def test_collections_query_ids_not_exists(
    user_api_client, published_collection, channel_USD
):
    query = NOT_EXISTS_IDS_COLLECTIONS_QUERY
    variables = {
        "filter": {"ids": ["ncXc5tP7kmV6pxE=", "yMyDVE5S2LWWTqK="]},
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response, ignore_errors=True)
    message_error = '{"ids": [{"message": "Invalid ID specified.", "code": ""}]}'

    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == message_error
    assert content["data"]["collections"] is None


FETCH_COLLECTION_QUERY = """
    query fetchCollection(
        $id: ID!, $channel: String,  $size: Int, $format: ThumbnailFormatEnum
    ){
        collection(id: $id, channel: $channel) {
            name
            backgroundImage(size: $size, format: $format) {
               url
               alt
            }
        }
    }
"""


def test_collection_image_query_with_size_and_format_proxy_url_returned(
    user_api_client, published_collection, media_root, channel_USD
):
    # given
    alt_text = "Alt text for an image."
    collection = published_collection
    image_file, image_name = create_image()
    background_mock = MagicMock(spec=File)
    background_mock.name = "image.jpg"
    collection.background_image = background_mock
    collection.background_image_alt = alt_text
    collection.save(update_fields=["background_image", "background_image_alt"])

    format = ThumbnailFormatEnum.WEBP.name

    collection_id = graphene.Node.to_global_id("Collection", collection.pk)
    variables = {
        "id": collection_id,
        "channel": channel_USD.slug,
        "size": 120,
        "format": format,
    }

    # when
    response = user_api_client.post_graphql(FETCH_COLLECTION_QUERY, variables)

    # then
    content = get_graphql_content(response)

    data = content["data"]["collection"]
    assert data["backgroundImage"]["alt"] == alt_text
    expected_url = (
        f"http://{TEST_SERVER_DOMAIN}/thumbnail/{collection_id}/128/{format.lower()}/"
    )
    assert data["backgroundImage"]["url"] == expected_url


def test_collection_image_query_with_size_proxy_url_returned(
    user_api_client, published_collection, media_root, channel_USD
):
    # given
    alt_text = "Alt text for an image."
    collection = published_collection
    background_mock = MagicMock(spec=File)
    background_mock.name = "image.jpg"
    collection.background_image = background_mock
    collection.background_image_alt = alt_text
    collection.save(update_fields=["background_image", "background_image_alt"])

    size = 128
    collection_id = graphene.Node.to_global_id("Collection", collection.pk)
    variables = {
        "id": collection_id,
        "channel": channel_USD.slug,
        "size": size,
    }

    # when
    response = user_api_client.post_graphql(FETCH_COLLECTION_QUERY, variables)

    # then
    content = get_graphql_content(response)

    data = content["data"]["collection"]
    assert data["backgroundImage"]["alt"] == alt_text
    assert (
        data["backgroundImage"]["url"]
        == f"http://{TEST_SERVER_DOMAIN}/thumbnail/{collection_id}/{size}/"
    )


def test_collection_image_query_with_size_thumbnail_url_returned(
    user_api_client, published_collection, media_root, channel_USD
):
    # given
    alt_text = "Alt text for an image."
    collection = published_collection
    background_mock = MagicMock(spec=File)
    background_mock.name = "image.jpg"
    collection.background_image = background_mock
    collection.background_image_alt = alt_text
    collection.save(update_fields=["background_image", "background_image_alt"])

    size = 128
    thumbnail_mock = MagicMock(spec=File)
    thumbnail_mock.name = "thumbnail_image.jpg"
    Thumbnail.objects.create(collection=collection, size=size, image=thumbnail_mock)

    collection_id = graphene.Node.to_global_id("Collection", collection.pk)
    variables = {
        "id": collection_id,
        "channel": channel_USD.slug,
        "size": 120,
    }

    # when
    response = user_api_client.post_graphql(FETCH_COLLECTION_QUERY, variables)

    # then
    content = get_graphql_content(response)

    data = content["data"]["collection"]
    assert data["backgroundImage"]["alt"] == alt_text
    assert (
        data["backgroundImage"]["url"]
        == f"http://{TEST_SERVER_DOMAIN}/media/thumbnails/{thumbnail_mock.name}"
    )


def test_collection_image_query_only_format_provided_original_image_returned(
    user_api_client, published_collection, media_root, channel_USD
):
    # given
    alt_text = "Alt text for an image."
    collection = published_collection
    background_mock = MagicMock(spec=File)
    background_mock.name = "image.jpg"
    collection.background_image = background_mock
    collection.background_image_alt = alt_text
    collection.save(update_fields=["background_image", "background_image_alt"])

    format = ThumbnailFormatEnum.WEBP.name

    collection_id = graphene.Node.to_global_id("Collection", collection.pk)
    variables = {
        "id": collection_id,
        "channel": channel_USD.slug,
        "format": format,
    }

    # when
    response = user_api_client.post_graphql(FETCH_COLLECTION_QUERY, variables)

    # then
    content = get_graphql_content(response)

    data = content["data"]["collection"]
    assert data["backgroundImage"]["alt"] == alt_text
    expected_url = (
        f"http://{TEST_SERVER_DOMAIN}"
        f"/media/collection-backgrounds/{background_mock.name}"
    )
    assert data["backgroundImage"]["url"] == expected_url


def test_collection_image_query_no_size_value_original_image_returned(
    user_api_client, published_collection, media_root, channel_USD
):
    # given
    alt_text = "Alt text for an image."
    collection = published_collection
    background_mock = MagicMock(spec=File)
    background_mock.name = "image.jpg"
    collection.background_image = background_mock
    collection.background_image_alt = alt_text
    collection.save(update_fields=["background_image", "background_image_alt"])

    collection_id = graphene.Node.to_global_id("Collection", collection.pk)
    variables = {
        "id": collection_id,
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(FETCH_COLLECTION_QUERY, variables)

    # then
    content = get_graphql_content(response)

    data = content["data"]["collection"]
    assert data["backgroundImage"]["alt"] == alt_text
    expected_url = (
        f"http://{TEST_SERVER_DOMAIN}"
        f"/media/collection-backgrounds/{background_mock.name}"
    )
    assert data["backgroundImage"]["url"] == expected_url


def test_collection_image_query_without_associated_file(
    user_api_client, published_collection, channel_USD
):
    # given
    collection = published_collection
    collection_id = graphene.Node.to_global_id("Collection", collection.pk)
    variables = {"id": collection_id, "channel": channel_USD.slug}

    # when
    response = user_api_client.post_graphql(FETCH_COLLECTION_QUERY, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["collection"]
    assert data["name"] == collection.name
    assert data["backgroundImage"] is None


def test_collection_query_invalid_id(
    user_api_client, published_collection, channel_USD
):
    collection_id = "'"
    variables = {
        "id": collection_id,
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(FETCH_COLLECTION_QUERY, variables)
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == f"Couldn't resolve id: {collection_id}."
    assert content["data"]["collection"] is None


def test_collection_query_object_with_given_id_does_not_exist(
    user_api_client, published_collection, channel_USD
):
    collection_id = graphene.Node.to_global_id("Collection", -1)
    variables = {
        "id": collection_id,
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(FETCH_COLLECTION_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["collection"] is None


def test_collection_query_object_with_invalid_object_type(
    user_api_client, published_collection, channel_USD
):
    collection_id = graphene.Node.to_global_id("Product", published_collection.pk)
    variables = {
        "id": collection_id,
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(FETCH_COLLECTION_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["collection"] is None


def test_update_collection_mutation_remove_background_image(
    staff_api_client, collection_with_image, permission_manage_products
):
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
        "id": to_global_id("Collection", collection_with_image.id),
        "backgroundImage": None,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["collectionUpdate"]["collection"]
    assert not data["backgroundImage"]
    collection_with_image.refresh_from_db()
    assert not collection_with_image.background_image


def _fetch_collection(client, collection, channel_slug, permissions=None):
    query = """
    query fetchCollection($id: ID!, $channel: String){
        collection(id: $id, channel: $channel) {
            name,
            channelListings {
                isPublished
            }
        }
    }
    """
    variables = {
        "id": graphene.Node.to_global_id("Collection", collection.id),
        "channel": channel_slug,
    }
    response = client.post_graphql(
        query, variables, permissions=permissions, check_no_permissions=False
    )
    content = get_graphql_content(response)
    return content["data"]["collection"]


def test_fetch_unpublished_collection_staff_user(
    staff_api_client, unpublished_collection, permission_manage_products, channel_USD
):
    collection_data = _fetch_collection(
        staff_api_client,
        unpublished_collection,
        channel_USD.slug,
        permissions=[permission_manage_products],
    )
    assert collection_data["name"] == unpublished_collection.name
    assert collection_data["channelListings"][0]["isPublished"] is False


def test_fetch_unpublished_collection_customer(
    user_api_client, unpublished_collection, channel_USD
):
    collection_data = _fetch_collection(
        user_api_client, unpublished_collection, channel_USD.slug
    )
    assert collection_data is None


def test_fetch_unpublished_collection_anonymous_user(
    api_client, unpublished_collection, channel_USD
):
    collection_data = _fetch_collection(
        api_client, unpublished_collection, channel_USD.slug
    )
    assert collection_data is None


GET_SORTED_PRODUCTS_COLLECTION_QUERY = """
query CollectionProducts($id: ID!, $channel: String, $sortBy: ProductOrder) {
  collection(id: $id, channel: $channel) {
    products(first: 10, sortBy: $sortBy) {
      edges {
        node {
          id
        }
      }
    }
  }
}
"""


def test_sort_collection_products_by_name(
    staff_api_client, published_collection, product_list, channel_USD
):
    # given
    for product in product_list:
        published_collection.products.add(product)

    variables = {
        "id": graphene.Node.to_global_id("Collection", published_collection.pk),
        "sortBy": {"direction": "DESC", "field": "NAME"},
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(
        GET_SORTED_PRODUCTS_COLLECTION_QUERY, variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["collection"]["products"]["edges"]

    assert [node["node"]["id"] for node in data] == [
        graphene.Node.to_global_id("Product", product.pk)
        for product in Product.objects.order_by("-name")
    ]


GET_SORTED_COLLECTION_QUERY = """
query Collections($sortBy: CollectionSortingInput) {
  collections(first: 10, sortBy: $sortBy) {
      edges {
        node {
          id
          publicationDate
        }
      }
  }
}
"""


def test_query_collection_for_federation(api_client, published_collection, channel_USD):
    collection_id = graphene.Node.to_global_id("Collection", published_collection.pk)
    variables = {
        "representations": [
            {
                "__typename": "Collection",
                "id": collection_id,
                "channel": channel_USD.slug,
            },
        ],
    }
    query = """
      query GetCollectionInFederation($representations: [_Any]) {
        _entities(representations: $representations) {
          __typename
          ... on Collection {
            id
            name
          }
        }
      }
    """

    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [
        {
            "__typename": "Collection",
            "id": collection_id,
            "name": published_collection.name,
        }
    ]
