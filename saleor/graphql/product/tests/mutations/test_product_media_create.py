import json
import os
from unittest.mock import Mock, patch

import graphene
import pytest
from django.conf import settings
from requests import RequestException
from requests.exceptions import InvalidSchema
from requests_hardened.ip_filter import InvalidIPAddress

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
                message
            }
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.product_media_created")
@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_product_media_create_mutation(
    product_updated_mock,
    product_media_created,
    monkeypatch,
    staff_api_client,
    product,
    permission_manage_products,
    media_root,
):
    # given
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

    # when
    response = staff_api_client.post_multipart(body)
    get_graphql_content(response)

    # then
    product.refresh_from_db()
    product_image = product.media.last()
    assert product_image.image.file
    img_name, format = os.path.splitext(image_file._name)
    file_name = product_image.image.name
    assert file_name != image_file._name
    assert file_name.startswith(f"products/{img_name}")
    assert file_name.endswith(format)

    product_updated_mock.assert_called_once_with(product)
    product_media_created.assert_called_once_with(product_image)


def test_product_media_create_mutation_file_size_exceeds_limit(
    staff_api_client, product, permission_manage_products, media_root, settings
):
    # given
    settings.MAX_IMAGE_FILE_SIZE = 1
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

    # when
    response = staff_api_client.post_multipart(body)
    content = get_graphql_content(response)

    # then
    errors = content["data"]["productMediaCreate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "image"
    assert errors[0]["code"] == ProductErrorCode.FILE_SIZE_LIMIT_EXCEEDED.name
    assert "File size exceeds the maximum allowed size" in errors[0]["message"]
    assert product.media.count() == 0


def test_product_media_create_mutation_without_file(
    monkeypatch, staff_api_client, product, permission_manage_products, media_root
):
    # given
    variables = {
        "product": graphene.Node.to_global_id("Product", product.id),
        "image": "image name",
    }
    body = get_multipart_request_body(
        PRODUCT_MEDIA_CREATE_QUERY, variables, file="", file_name="name"
    )

    # when
    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["productMediaCreate"]["errors"]
    assert errors[0]["field"] == "image"
    assert errors[0]["code"] == ProductErrorCode.REQUIRED.name


@patch("saleor.graphql.product.utils.HTTPClient")
@pytest.mark.vcr
def test_product_media_create_mutation_with_media_url(
    mock_HTTPClient, staff_api_client, product, permission_manage_products, media_root
):
    # given
    mock_response = Mock()
    mock_response.headers.get = Mock(return_value="text/html; charset=utf-8")
    mock_HTTPClient.send_request.return_value.__enter__.return_value = mock_response
    variables = {
        "product": graphene.Node.to_global_id("Product", product.id),
        "mediaUrl": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "alt": "",
    }
    body = get_multipart_request_body(
        PRODUCT_MEDIA_CREATE_QUERY, variables, file="", file_name="name"
    )

    # when
    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    # then
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
    # given
    variables = {
        "product": graphene.Node.to_global_id("Product", product.id),
        "alt": "Test Alt Text",
    }
    body = get_multipart_request_body(
        PRODUCT_MEDIA_CREATE_QUERY, variables, file="", file_name="name"
    )

    # when
    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["productMediaCreate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == ProductErrorCode.REQUIRED.name
    assert errors[0]["field"] == "input"


def test_product_media_create_mutation_with_both_url_and_image(
    monkeypatch, staff_api_client, product, permission_manage_products, media_root
):
    # given
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

    # when
    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["productMediaCreate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == ProductErrorCode.DUPLICATED_INPUT_ITEM.name
    assert errors[0]["field"] == "input"


@patch("saleor.graphql.product.utils.HTTPClient")
def test_product_media_create_mutation_with_unknown_url(
    mock_HTTPClient, staff_api_client, product, permission_manage_products, media_root
):
    # given
    mock_response = Mock()
    mock_response.headers.get = Mock(return_value="text/html; charset=utf-8")
    mock_HTTPClient.send_request.return_value.__enter__.return_value = mock_response
    variables = {
        "product": graphene.Node.to_global_id("Product", product.id),
        "mediaUrl": "https://www.videohosting.com/SomeVideoID",
        "alt": "Test Alt Text",
    }
    body = get_multipart_request_body(
        PRODUCT_MEDIA_CREATE_QUERY, variables, file="", file_name="name"
    )

    # when
    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["productMediaCreate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == ProductErrorCode.UNSUPPORTED_MEDIA_PROVIDER.name
    assert errors[0]["field"] == "mediaUrl"


def test_invalid_product_media_create_mutation(
    staff_api_client, product, permission_manage_products
):
    # given
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

    # when
    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    # then
    assert content["data"]["productMediaCreate"]["errors"] == [
        {"field": "image", "message": "Invalid file type."}
    ]
    product.refresh_from_db()
    assert product.media.count() == 0


@patch("saleor.graphql.product.utils.HTTPClient")
def test_product_media_create_mutation_invalid_image_file_fetch_only_header(
    mock_HTTPClient, staff_api_client, product, permission_manage_products
):
    # given
    mock_response = Mock()
    mock_response.headers = Mock()
    mock_response.headers.get = Mock(return_value="image/not-supported")
    mock_response.raw = Mock()
    mock_response.raw.read = Mock(return_value=b"fake_image_data")
    mock_HTTPClient.send_request.return_value.__enter__.return_value = mock_response

    url = "https://saleor.io/invalid.png"
    variables = {
        "product": graphene.Node.to_global_id("Product", product.id),
        "mediaUrl": url,
        "alt": "",
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_CREATE_QUERY,
        variables=variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["productMediaCreate"]["errors"]
    assert errors[0]["field"] == "mediaUrl"
    assert errors[0]["code"] == ProductErrorCode.INVALID.name

    # Ensure that the file content was not fetched
    mock_response.raw.read.assert_not_called()
    mock_response.raw.assert_not_called()

    # Ensure that only headers were fetched
    mock_HTTPClient.send_request.assert_called_once_with(
        "GET",
        url,
        stream=True,
        allow_redirects=False,
        timeout=settings.COMMON_REQUESTS_TIMEOUT,
    )
    mock_response.headers.get.assert_called_once_with("content-type")


@patch(
    "saleor.graphql.product.mutations.product.product_media_create.fetch_product_media_image_task.delay"
)
@pytest.mark.vcr
def test_product_media_create_mutation_valid_image_file_is_fetched_once(
    mock_fetch_product_media_image_task,
    staff_api_client,
    product,
    permission_manage_products,
    media_root,
):
    # given
    expected_file_name = "icon-dark.png"
    url = f"https://saleor.io/{expected_file_name}"
    expected_alt = "Icon Dark"
    variables = {
        "product": graphene.Node.to_global_id("Product", product.id),
        "mediaUrl": url,
        "alt": expected_alt,
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_CREATE_QUERY,
        variables=variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productMediaCreate"]
    assert data["errors"] == []
    assert data["product"]["media"][0]["type"] == ProductMediaTypes.IMAGE
    assert data["product"]["media"][0]["alt"] == expected_alt
    assert data["product"]["media"][0]["url"] != url

    product.refresh_from_db()
    product_image = product.media.last()

    assert bool(product_image.image) is False
    assert product_image.external_url is not None
    mock_fetch_product_media_image_task.assert_called_once_with(product_image.pk)


@patch(
    "saleor.graphql.product.mutations.product.product_media_create.fetch_product_media_image_task.delay"
)
@patch("saleor.graphql.product.utils.HTTPClient")
def test_product_media_create_mutation_with_no_extension_media_url(
    mock_HTTPClient,
    mock_fetch_product_media_image_task,
    staff_api_client,
    product,
    permission_manage_products,
    media_root,
):
    # given
    mock_response = Mock()
    mock_response.headers.get = Mock(return_value="image/png")
    mock_HTTPClient.send_request.return_value.__enter__.return_value = mock_response
    variables = {
        "product": graphene.Node.to_global_id("Product", product.id),
        "mediaUrl": "https://saleor.io/image-path",
        "alt": "",
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_CREATE_QUERY,
        variables=variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)["data"]["productMediaCreate"]

    # then
    assert not content["errors"]
    product_image = product.media.last()

    assert bool(product_image.image) is False
    assert product_image.external_url is not None
    mock_fetch_product_media_image_task.assert_called_once_with(product_image.pk)


def test_product_media_create_mutation_alt_character_limit(
    monkeypatch, staff_api_client, product, permission_manage_products, media_root
):
    alt_260_chars = """
    Lorem ipsum dolor sit amet, consectetuer adipiscing elit.
    Aenean commodo ligula eget dolor. Aenean massa. Cym sociis natoque penatibus et
    magnis dis parturient montes, nascetur ridiculus mus. Donec quam felis, ultricies
    nec, pellentesque eu, pretium quis, sem.
    """
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    image_file, image_name = create_image()
    variables = {
        "product": graphene.Node.to_global_id("Product", product.id),
        "alt": alt_260_chars,
        "image": image_name,
    }
    body = get_multipart_request_body(
        PRODUCT_MEDIA_CREATE_QUERY, variables, image_file, image_name
    )

    # when
    response = staff_api_client.post_multipart(body)
    content = get_graphql_content(response)

    # then

    errors = content["data"]["productMediaCreate"]["errors"]
    assert errors[0]["field"] == "input"
    assert errors[0]["code"] == ProductErrorCode.INVALID.name


def test_product_media_create_when_alt_is_null(
    staff_api_client, product, permission_manage_products, media_root
):
    # given
    image_file, image_name = create_image()
    variables = {
        "product": graphene.Node.to_global_id("Product", product.id),
        "alt": None,
        "image": image_name,
    }

    # when
    body = get_multipart_request_body(
        PRODUCT_MEDIA_CREATE_QUERY, variables, image_file, image_name
    )
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_multipart(body)
    content = get_graphql_content(response)["data"]["productMediaCreate"]

    # then
    assert not content["errors"]
    assert content["product"]["media"][0]["alt"] == ""


@patch(
    "saleor.graphql.product.mutations.product.product_media_create.fetch_product_media_image_task.delay"
)
@patch("saleor.graphql.product.utils.HTTPClient")
def test_product_media_create_with_media_url_when_alt_is_null(
    mock_HTTPClient,
    mock_fetch_product_media_image_task,
    staff_api_client,
    product,
    permission_manage_products,
    media_root,
):
    # given
    image_file, _ = create_image()
    mock_response = Mock()
    mock_response.headers.get.return_value = image_file.content_type
    mock_response.content = image_file.read()
    mock_HTTPClient.send_request.return_value.__enter__.return_value = mock_response
    variables = {
        "product": graphene.Node.to_global_id("Product", product.id),
        "mediaUrl": "https://saleor.io/image-path",
        "alt": None,
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_CREATE_QUERY,
        variables=variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)["data"]["productMediaCreate"]

    # then
    assert not content["errors"]
    assert content["product"]["media"][0]["alt"] == ""

    product_media = product.media.last()
    mock_fetch_product_media_image_task.assert_called_once_with(product_media.pk)


@pytest.mark.parametrize(
    "exception",
    [
        RequestException("Connection refused"),
        InvalidIPAddress("10.0.0.1"),
        InvalidSchema("No adapters found for url"),
    ],
)
@patch("saleor.graphql.product.utils.HTTPClient")
def test_product_media_create_mutation_request_exception(
    mock_HTTPClient,
    exception,
    staff_api_client,
    product,
    permission_manage_products,
):
    # given
    mock_HTTPClient.send_request.side_effect = exception
    variables = {
        "product": graphene.Node.to_global_id("Product", product.id),
        "mediaUrl": "https://www.example.com/image.jpg",
        "alt": "some media",
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_CREATE_QUERY,
        variables=variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    # then
    assert len(content["data"]["productMediaCreate"]["errors"]) == 1
    error = content["data"]["productMediaCreate"]["errors"][0]
    assert error["code"] == ProductErrorCode.INVALID.name
    assert error["field"] == "mediaUrl"
    assert error["message"] == "Failed to fetch media from URL."


def test_product_media_create_mutation_with_empty_product_id(
    staff_api_client, permission_manage_products
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    variables = {
        "product": "",
        "mediaUrl": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_CREATE_QUERY,
        variables=variables,
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["productMediaCreate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "product"
    assert errors[0]["code"] == ProductErrorCode.REQUIRED.name
