import os
from unittest.mock import patch

import graphene
import pytest

from .....product.models import Collection
from .....product.tests.utils import create_image
from .....tests.utils import dummy_editorjs
from ....tests.utils import (
    get_graphql_content,
    get_multipart_request_body,
)

CREATE_COLLECTION_MUTATION = """
    mutation createCollection(
            $name: String!, $slug: String,
            $description: JSONString, $products: [ID!],
            $backgroundImage: Upload, $backgroundImageAlt: String
            $metadata: [MetadataInput!], $privateMetadata: [MetadataInput!]) {
        collectionCreate(
            input: {
                name: $name,
                slug: $slug,
                description: $description,
                products: $products,
                backgroundImage: $backgroundImage,
                backgroundImageAlt: $backgroundImageAlt
                metadata: $metadata
                privateMetadata: $privateMetadata
                }) {
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
                metadata {
                    key
                    value
                }
                privateMetadata {
                    key
                    value
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
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)

    product_ids = [
        graphene.Node.to_global_id("Product", product.pk) for product in product_list
    ]
    image_file, image_name = create_image()
    image_alt = "Alt text for an image."
    name = "test-name"
    slug = "test-slug"
    description = dummy_editorjs("description", True)
    metadata_key = "md key"
    metadata_value = "md value"

    variables = {
        "name": name,
        "slug": slug,
        "description": description,
        "products": product_ids,
        "backgroundImage": image_name,
        "backgroundImageAlt": image_alt,
        "metadata": [{"key": metadata_key, "value": metadata_value}],
        "privateMetadata": [{"key": metadata_key, "value": metadata_value}],
    }
    body = get_multipart_request_body(
        CREATE_COLLECTION_MUTATION, variables, image_file, image_name
    )

    # when
    response = staff_api_client.post_multipart(body)
    content = get_graphql_content(response)
    data = content["data"]["collectionCreate"]["collection"]

    # then
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
    assert collection.metadata == {metadata_key: metadata_value}
    assert collection.private_metadata == {metadata_key: metadata_value}

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

    product_ids = [
        graphene.Node.to_global_id("Product", product.pk) for product in product_list
    ]
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
    ("input_slug", "expected_slug"),
    [
        ("test-slug", "test-slug"),
        (None, "test-collection"),
        ("", "test-collection"),
        ("わたし-わ-にっぽん-です", "わたし-わ-にっぽん-です"),
    ],
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
