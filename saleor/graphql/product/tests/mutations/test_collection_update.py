from unittest.mock import MagicMock, Mock, patch

import graphene
import pytest
from django.core.files import File

from .....product.error_codes import ProductErrorCode
from .....product.models import Collection
from .....product.tests.utils import create_image, create_zip_file_with_image_ext
from .....tests.utils import dummy_editorjs
from .....thumbnail.models import Thumbnail
from ....tests.utils import (
    get_graphql_content,
    get_multipart_request_body,
)


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
    # given
    query = """
        mutation updateCollection(
            $name: String!, $slug: String!, $description: JSONString, $id: ID!,
            $metadata: [MetadataInput!], $privateMetadata: [MetadataInput!]
            ) {

            collectionUpdate(
                id: $id, input: {
                    name: $name, slug: $slug, description: $description,
                    metadata: $metadata, privateMetadata: $privateMetadata
                }) {

                collection {
                    name
                    slug
                    description
                    metadata {
                        key
                        value
                    }
                    privateMetadata {
                        key
                        value
                    }
                }
            }
        }
    """
    description = dummy_editorjs("test description", True)
    old_meta = {"old": "meta"}
    collection.store_value_in_metadata(items=old_meta)
    collection.store_value_in_private_metadata(items=old_meta)
    collection.save(update_fields=["metadata", "private_metadata"])
    metadata_key = "md key"
    metadata_value = "md value"

    name = "new-name"
    slug = "new-slug"
    description = description
    variables = {
        "name": name,
        "slug": slug,
        "description": description,
        "id": graphene.Node.to_global_id("Collection", collection.id),
        "metadata": [{"key": metadata_key, "value": metadata_value}],
        "privateMetadata": [{"key": metadata_key, "value": metadata_value}],
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["collectionUpdate"]["collection"]
    collection.refresh_from_db()

    # then
    assert data["name"] == name
    assert data["slug"] == slug
    assert collection.metadata == {metadata_key: metadata_value, **old_meta}
    assert collection.private_metadata == {metadata_key: metadata_value, **old_meta}

    created_webhook_mock.assert_not_called()
    updated_webhook_mock.assert_called_once()


def test_update_collection_metadata_marks_prices_to_recalculate(
    staff_api_client,
    collection,
    permission_manage_products,
    catalogue_promotion,
    product,
):
    # given
    query = """
        mutation updateCollection(
            $id: ID!,
            $metadata: [MetadataInput!]
            ) {

            collectionUpdate(
                id: $id, input: {
                    metadata: $metadata,
                }) {

                collection {
                    name
                    slug
                    description
                    metadata {
                        key
                        value
                    }
                    privateMetadata {
                        key
                        value
                    }
                }
            }
        }
    """
    metadata_key = "md key"
    metadata_value = "md value"

    collection.products.set([product])

    variables = {
        "id": graphene.Node.to_global_id("Collection", collection.id),
        "metadata": [{"key": metadata_key, "value": metadata_value}],
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    get_graphql_content(response)

    collection.refresh_from_db()

    # then
    assert not catalogue_promotion.rules.filter(variants_dirty=False).exists()


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
                backgroundImage(size: 0) {
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
    staff_api_client.user.user_permissions.add(permission_manage_products)

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
        "id": graphene.Node.to_global_id("Collection", collection.id),
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
    response = staff_api_client.post_multipart(body)

    # then
    content = get_graphql_content(response)
    data = content["data"]["collectionUpdate"]
    assert not data["errors"]
    slug = data["collection"]["slug"]
    collection = Collection.objects.get(slug=slug)
    assert data["collection"]["backgroundImage"]["alt"] == image_alt
    assert data["collection"]["backgroundImage"]["url"].startswith(
        f"https://example.com/media/collection-backgrounds/{image_name}"
    )

    # ensure that thumbnails for old background image has been deleted
    assert not Thumbnail.objects.filter(collection_id=collection.id)
    delete_from_storage_task_mock.assert_called_once_with(img_path)


@patch("saleor.core.tasks.delete_from_storage_task.delay")
def test_update_collection_invalid_background_image_content_type(
    delete_from_storage_task_mock,
    staff_api_client,
    collection,
    permission_manage_products,
    media_root,
):
    # given
    image_file, image_name = create_zip_file_with_image_ext()
    image_alt = "Alt text for an image."

    size = 128
    thumbnail_mock = MagicMock(spec=File)
    thumbnail_mock.name = "thumbnail_image.jpg"
    Thumbnail.objects.create(collection=collection, size=size, image=thumbnail_mock)

    variables = {
        "name": "new-name",
        "slug": "new-slug",
        "id": graphene.Node.to_global_id("Collection", collection.id),
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


@patch("saleor.core.tasks.delete_from_storage_task.delay")
def test_update_collection_invalid_background_image(
    delete_from_storage_task_mock,
    monkeypatch,
    staff_api_client,
    collection,
    permission_manage_products,
    media_root,
):
    # given
    image_file, image_name = create_image()
    image_alt = "Alt text for an image."

    error_msg = "Test syntax error"
    image_file_mock = Mock(side_effect=SyntaxError(error_msg))
    monkeypatch.setattr(
        "saleor.graphql.core.validators.file.Image.open", image_file_mock
    )

    size = 128
    thumbnail_mock = MagicMock(spec=File)
    thumbnail_mock.name = "thumbnail_image.jpg"
    Thumbnail.objects.create(collection=collection, size=size, image=thumbnail_mock)

    variables = {
        "name": "new-name",
        "slug": "new-slug",
        "id": graphene.Node.to_global_id("Collection", collection.id),
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
    assert error_msg in data["errors"][0]["message"]

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
    ("input_slug", "expected_slug", "error_message"),
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

    Node_id = graphene.Node.to_global_id("Collection", collection.id)
    variables = {"slug": input_slug, "id": Node_id}
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

    Node_id = graphene.Node.to_global_id("Collection", collection.id)
    variables = {"slug": input_slug, "id": Node_id}
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
    ("input_slug", "expected_slug", "input_name", "error_message", "error_field"),
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

    Node_id = graphene.Node.to_global_id("Collection", collection.id)
    variables = {"slug": input_slug, "name": input_name, "id": Node_id}
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
        "id": graphene.Node.to_global_id("Collection", collection_with_image.id),
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
