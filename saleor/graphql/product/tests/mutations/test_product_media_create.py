import json
import os
from unittest.mock import patch

import graphene
import pytest

from .....graphql.tests.utils import get_graphql_content, get_multipart_request_body
from .....product import ProductMediaTypes
from .....product.error_codes import ProductErrorCode
from .....product.tests.utils import create_image, create_zip_file_with_image_ext

PRODUCT_MEDIA_CREATE_QUERY = """
    mutation createProductMedia(
        $product: ID!,
        $image: Upload,
        $mediaUrl: String,
        $alt: String
    ) {
        productMediaCreate(input: {
            product: $product,
            mediaUrl: $mediaUrl,
            alt: $alt,
            image: $image
        }) {
            product {
                media {
                    url
                    alt
                    type
                    oembedData
                }
            }
            errors {
                code
                field
            }
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_product_media_create_mutation(
    product_updated_mock,
    monkeypatch,
    staff_api_client,
    product,
    permission_manage_products,
    media_root,
):
    staff_api_client.user.user_permissions.add(permission_manage_products)
    image_file, image_name = create_image()
    variables = {
        "product": graphene.Node.to_global_id("Product", product.id),
        "alt": "",
        "image": image_name,
    }
    body = get_multipart_request_body(
        PRODUCT_MEDIA_CREATE_QUERY, variables, image_file, image_name
    )
    response = staff_api_client.post_multipart(body)
    get_graphql_content(response)
    product.refresh_from_db()
    product_image = product.media.last()
    assert product_image.image.file
    img_name, format = os.path.splitext(image_file._name)
    file_name = product_image.image.name
    assert file_name != image_file._name
    assert file_name.startswith(f"products/{img_name}")
    assert file_name.endswith(format)

    product_updated_mock.assert_called_once_with(product)


def test_product_media_create_mutation_without_file(
    monkeypatch, staff_api_client, product, permission_manage_products, media_root
):
    variables = {
        "product": graphene.Node.to_global_id("Product", product.id),
        "image": "image name",
    }
    body = get_multipart_request_body(
        PRODUCT_MEDIA_CREATE_QUERY, variables, file="", file_name="name"
    )
    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    errors = content["data"]["productMediaCreate"]["errors"]
    assert errors[0]["field"] == "image"
    assert errors[0]["code"] == ProductErrorCode.REQUIRED.name


@pytest.mark.vcr
def test_product_media_create_mutation_with_media_url(
    monkeypatch, staff_api_client, product, permission_manage_products, media_root
):
    variables = {
        "product": graphene.Node.to_global_id("Product", product.id),
        "mediaUrl": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "alt": "",
    }
    body = get_multipart_request_body(
        PRODUCT_MEDIA_CREATE_QUERY, variables, file="", file_name="name"
    )
    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    media = content["data"]["productMediaCreate"]["product"]["media"]
    alt = "Rick Astley - Never Gonna Give You Up (Official Music Video)"

    assert len(media) == 1
    assert media[0]["url"] == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert media[0]["alt"] == alt
    assert media[0]["type"] == ProductMediaTypes.VIDEO

    oembed_data = json.loads(media[0]["oembedData"])
    assert oembed_data["url"] == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert oembed_data["type"] == "video"
    assert oembed_data["html"] is not None
    assert oembed_data["thumbnail_url"] == (
        "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg"
    )


def test_product_media_create_mutation_without_url_or_image(
    monkeypatch, staff_api_client, product, permission_manage_products, media_root
):
    variables = {
        "product": graphene.Node.to_global_id("Product", product.id),
        "alt": "Test Alt Text",
    }
    body = get_multipart_request_body(
        PRODUCT_MEDIA_CREATE_QUERY, variables, file="", file_name="name"
    )

    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products]
    )

    content = get_graphql_content(response)
    errors = content["data"]["productMediaCreate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == ProductErrorCode.REQUIRED.name
    assert errors[0]["field"] == "input"


def test_product_media_create_mutation_with_both_url_and_image(
    monkeypatch, staff_api_client, product, permission_manage_products, media_root
):
    image_file, image_name = create_image()
    variables = {
        "product": graphene.Node.to_global_id("Product", product.id),
        "mediaUrl": "https://www.youtube.com/watch?v=SomeVideoID&ab_channel=Test",
        "image": image_name,
        "alt": "Test Alt Text",
    }
    body = get_multipart_request_body(
        PRODUCT_MEDIA_CREATE_QUERY, variables, image_file, image_name
    )

    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products]
    )

    content = get_graphql_content(response)
    errors = content["data"]["productMediaCreate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == ProductErrorCode.DUPLICATED_INPUT_ITEM.name
    assert errors[0]["field"] == "input"


def test_product_media_create_mutation_with_unknown_url(
    monkeypatch, staff_api_client, product, permission_manage_products, media_root
):
    variables = {
        "product": graphene.Node.to_global_id("Product", product.id),
        "mediaUrl": "https://www.videohosting.com/SomeVideoID",
        "alt": "Test Alt Text",
    }
    body = get_multipart_request_body(
        PRODUCT_MEDIA_CREATE_QUERY, variables, file="", file_name="name"
    )

    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products]
    )

    content = get_graphql_content(response)
    errors = content["data"]["productMediaCreate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == ProductErrorCode.UNSUPPORTED_MEDIA_PROVIDER.name
    assert errors[0]["field"] == "mediaUrl"


def test_invalid_product_media_create_mutation(
    staff_api_client, product, permission_manage_products
):
    query = """
    mutation createProductMedia($image: Upload!, $product: ID!) {
        productMediaCreate(input: {image: $image, product: $product}) {
            media {
                id
                url
                sortOrder
            }
            errors {
                field
                message
            }
        }
    }
    """
    image_file, image_name = create_zip_file_with_image_ext()
    variables = {
        "product": graphene.Node.to_global_id("Product", product.id),
        "image": image_name,
    }
    body = get_multipart_request_body(query, variables, image_file, image_name)

    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products]
    )

    content = get_graphql_content(response)
    assert content["data"]["productMediaCreate"]["errors"] == [
        {"field": "image", "message": "Invalid file type."}
    ]
    product.refresh_from_db()
    assert product.media.count() == 0


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_product_image_update_mutation(
    product_updated_mock,
    monkeypatch,
    staff_api_client,
    product_with_image,
    permission_manage_products,
):
    query = """
    mutation updateProductMedia($mediaId: ID!, $alt: String) {
        productMediaUpdate(id: $mediaId, input: {alt: $alt}) {
            media {
                alt
            }
        }
    }
    """

    media_obj = product_with_image.media.first()
    alt = "damage alt"
    variables = {
        "alt": alt,
        "mediaId": graphene.Node.to_global_id("ProductMedia", media_obj.id),
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    assert content["data"]["productMediaUpdate"]["media"]["alt"] == alt

    product_updated_mock.assert_called_once_with(product_with_image)


@patch("saleor.plugins.manager.PluginsManager.product_updated")
@patch("saleor.product.signals.delete_from_storage_task.delay")
def test_product_media_delete(
    delete_from_storage_task_mock,
    product_updated_mock,
    staff_api_client,
    product_with_image,
    permission_manage_products,
):
    product = product_with_image
    query = """
            mutation deleteProductMedia($id: ID!) {
                productMediaDelete(id: $id) {
                    media {
                        id
                        url
                    }
                }
            }
        """
    media_obj = product.media.first()
    media_img_path = media_obj.image.name
    node_id = graphene.Node.to_global_id("ProductMedia", media_obj.id)
    variables = {"id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productMediaDelete"]
    assert media_obj.image.url in data["media"]["url"]
    with pytest.raises(media_obj._meta.model.DoesNotExist):
        media_obj.refresh_from_db()
    assert node_id == data["media"]["id"]
    product_updated_mock.assert_called_once_with(product)
    delete_from_storage_task_mock.assert_called_once_with(media_img_path)
