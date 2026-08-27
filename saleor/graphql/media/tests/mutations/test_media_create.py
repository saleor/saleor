import os
from unittest.mock import Mock, patch

import graphene
import pytest

from .....graphql.tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
    get_multipart_request_body,
)
from .....product import MediaOwnerTypes, ProductMediaTypes
from .....product.error_codes import MediaCreateErrorCode
from .....product.media import (
    MEDIA_OWNER_PERMISSION_MAP,
    OWNER_TYPE_TO_GRAPHQL_TYPE,
    OWNER_TYPE_TO_MEDIA_GRAPHQL_TYPE,
)
from .....product.models import ProductMedia
from .....product.tests.utils import create_image

MEDIA_CREATE_MUTATION = """
    mutation createMedia($id: ID!, $image: Upload, $mediaUrl: String, $alt: String) {
        mediaCreate(id: $id, input: {
            image: $image, mediaUrl: $mediaUrl, alt: $alt
        }) {
            media {
                __typename
                id
                alt
                mediaType
                oembedData
                ownerType
                ownerId
            }
            errors {
                code
                field
                message
            }
        }
    }
"""

ALL_OWNER_TYPES = MediaOwnerTypes.ALL


@pytest.mark.parametrize("owner_type", ALL_OWNER_TYPES)
def test_create_with_image_upload(
    owner_type,
    media_owner,
    staff_api_client,
    permission_manage_products,
    permission_manage_pages,
    media_root,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_products, permission_manage_pages
    )
    image_file, image_name = create_image()
    owner_id = graphene.Node.to_global_id(
        OWNER_TYPE_TO_GRAPHQL_TYPE[owner_type], media_owner.pk
    )
    alt = "An alt text"
    variables = {"id": owner_id, "alt": alt, "image": image_name}
    body = get_multipart_request_body(
        MEDIA_CREATE_MUTATION, variables, image_file, image_name
    )

    # when
    response = staff_api_client.post_multipart(body)

    # then
    content = get_graphql_content(response)
    data = content["data"]["mediaCreate"]
    assert data["errors"] == []

    media = media_owner.media.get()
    assert media.alt == alt
    assert media.type == ProductMediaTypes.IMAGE
    img_name, extension = os.path.splitext(image_file._name)
    assert media.image.name.startswith(f"products/{img_name}")
    assert media.image.name.endswith(extension)

    assert data["media"]["__typename"] == OWNER_TYPE_TO_MEDIA_GRAPHQL_TYPE[owner_type]
    assert data["media"]["id"] == graphene.Node.to_global_id(
        OWNER_TYPE_TO_MEDIA_GRAPHQL_TYPE[owner_type], media.pk
    )
    assert data["media"]["alt"] == alt
    assert data["media"]["mediaType"] == ProductMediaTypes.IMAGE
    assert data["media"]["ownerType"] == owner_type.upper()
    assert data["media"]["ownerId"] == owner_id


@pytest.mark.parametrize("owner_type", ALL_OWNER_TYPES)
@patch("saleor.product.tasks.fetch_product_media_image_task.delay")
@patch("saleor.product.media.HTTPClient")
def test_create_with_remote_image_url(
    mock_http_client,
    mock_fetch_task,
    owner_type,
    media_owner,
    staff_api_client,
    permission_manage_products,
    permission_manage_pages,
    media_root,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_products, permission_manage_pages
    )
    mock_response = Mock()
    mock_response.headers.get = Mock(return_value="image/jpeg")
    mock_http_client.send_request.return_value.__enter__.return_value = mock_response
    media_url = "https://images.example.com/photo.jpg"
    variables = {
        "id": graphene.Node.to_global_id(
            OWNER_TYPE_TO_GRAPHQL_TYPE[owner_type], media_owner.pk
        ),
        "mediaUrl": media_url,
        "alt": "",
    }

    # when
    response = staff_api_client.post_graphql(MEDIA_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["mediaCreate"]
    assert data["errors"] == []

    media = media_owner.media.get()
    assert media.external_url == media_url
    assert media.type == ProductMediaTypes.IMAGE
    mock_fetch_task.assert_called_once_with(media.pk)


@pytest.mark.parametrize("owner_type", ALL_OWNER_TYPES)
@patch("saleor.product.media.get_oembed_data")
@patch("saleor.product.media.HTTPClient")
def test_create_with_oembed_url(
    mock_http_client,
    mock_get_oembed_data,
    owner_type,
    media_owner,
    staff_api_client,
    permission_manage_products,
    permission_manage_pages,
    media_root,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_products, permission_manage_pages
    )
    mock_response = Mock()
    mock_response.headers.get = Mock(return_value="text/html; charset=utf-8")
    mock_http_client.send_request.return_value.__enter__.return_value = mock_response
    media_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    oembed_data = {"url": media_url, "title": "A video"}
    mock_get_oembed_data.return_value = (oembed_data, ProductMediaTypes.VIDEO)
    variables = {
        "id": graphene.Node.to_global_id(
            OWNER_TYPE_TO_GRAPHQL_TYPE[owner_type], media_owner.pk
        ),
        "mediaUrl": media_url,
        "alt": "",
    }

    # when
    response = staff_api_client.post_graphql(MEDIA_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["mediaCreate"]
    assert data["errors"] == []
    assert data["media"]["mediaType"] == ProductMediaTypes.VIDEO

    media = media_owner.media.get()
    assert media.type == ProductMediaTypes.VIDEO
    assert media.alt == oembed_data["title"]
    assert media.oembed_data == oembed_data


@pytest.mark.parametrize("owner_type", ALL_OWNER_TYPES)
@patch("saleor.plugins.manager.PluginsManager.media_created")
def test_create_triggers_owner_and_media_events(
    mock_media_created,
    owner_type,
    media_owner,
    staff_api_client,
    permission_manage_products,
    permission_manage_pages,
    media_root,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_products, permission_manage_pages
    )
    image_file, image_name = create_image()
    variables = {
        "id": graphene.Node.to_global_id(
            OWNER_TYPE_TO_GRAPHQL_TYPE[owner_type], media_owner.pk
        ),
        "alt": "",
        "image": image_name,
    }
    body = get_multipart_request_body(
        MEDIA_CREATE_MUTATION, variables, image_file, image_name
    )
    owner_event = f"{owner_type}_updated"

    # when
    with patch(f"saleor.plugins.manager.PluginsManager.{owner_event}") as mock_owner:
        response = staff_api_client.post_multipart(body)

    # then
    get_graphql_content(response)
    media = media_owner.media.get()
    mock_media_created.assert_called_once_with(media)
    assert mock_owner.call_count == 1
    assert mock_owner.call_args.args[0].pk == media_owner.pk


@pytest.mark.parametrize(
    (
        "_case",
        "media_url",
        "alt",
        "expected_code",
        "expected_field",
        "expected_message",
    ),
    [
        (
            "no image and no url",
            None,
            "",
            MediaCreateErrorCode.REQUIRED.name,
            "input",
            "Image or external URL is required.",
        ),
        (
            "alt too long",
            "https://images.example.com/photo.jpg",
            "a" * 251,
            MediaCreateErrorCode.INVALID.name,
            "input",
            "Alt field exceeds the character limit of 250.",
        ),
    ],
)
def test_create_input_validation(
    _case,
    media_url,
    alt,
    expected_code,
    expected_field,
    expected_message,
    staff_api_client,
    page,
    permission_manage_pages,
    media_root,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_pages)
    variables = {
        "id": graphene.Node.to_global_id("Page", page.pk),
        "mediaUrl": media_url,
        "alt": alt,
    }

    # when
    response = staff_api_client.post_graphql(MEDIA_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    errors = content["data"]["mediaCreate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == expected_code
    assert errors[0]["field"] == expected_field
    assert errors[0]["message"] == expected_message
    assert ProductMedia.objects.exists() is False


def test_create_rejects_unsupported_owner_type(
    staff_api_client, order, permission_manage_products, permission_manage_pages
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_products, permission_manage_pages
    )
    variables = {
        "id": graphene.Node.to_global_id("Order", order.pk),
        "mediaUrl": "https://images.example.com/photo.jpg",
        "alt": "",
    }

    # when
    response = staff_api_client.post_graphql(MEDIA_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    errors = content["data"]["mediaCreate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == MediaCreateErrorCode.INVALID.name
    assert errors[0]["field"] == "id"
    assert errors[0]["message"] == (
        "Media can only be attached to a Product, Category, Collection or Page."
    )
    assert ProductMedia.objects.exists() is False


def test_create_rejects_missing_owner(
    staff_api_client, permission_manage_pages, media_root
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_pages)
    owner_id = graphene.Node.to_global_id("Page", -1)
    variables = {
        "id": owner_id,
        "mediaUrl": "https://images.example.com/photo.jpg",
        "alt": "",
    }

    # when
    response = staff_api_client.post_graphql(MEDIA_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    errors = content["data"]["mediaCreate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == MediaCreateErrorCode.NOT_FOUND.name
    assert errors[0]["field"] == "id"
    assert errors[0]["message"] == f"Couldn't resolve to an object: {owner_id}"
    assert ProductMedia.objects.exists() is False


@pytest.mark.parametrize("owner_type", ALL_OWNER_TYPES)
@pytest.mark.parametrize(
    ("_case", "client_fixture", "permission_fixture", "is_allowed"),
    [
        ("Unauthenticated user should be rejected", "api_client", None, False),
        ("Unprivileged user should be rejected", "user_api_client", None, False),
        (
            "Staff user without the permission should be rejected",
            "staff_api_client",
            None,
            False,
        ),
        (
            "Staff user with the owner's permission should be allowed",
            "staff_api_client",
            "owner",
            True,
        ),
        (
            "Staff user with the other domain's permission should be rejected",
            "staff_api_client",
            "other",
            False,
        ),
    ],
)
@patch("saleor.plugins.manager.PluginsManager.media_created")
def test_create_authorization(
    mock_media_created,
    _case,
    client_fixture,
    permission_fixture,
    is_allowed,
    owner_type,
    media_owner,
    request,
    media_root,
):
    # given
    client = request.getfixturevalue(client_fixture)
    owner_permission = MEDIA_OWNER_PERMISSION_MAP[owner_type]
    other_permission = next(
        permission
        for permission in MEDIA_OWNER_PERMISSION_MAP.values()
        if permission != owner_permission
    )
    if permission_fixture:
        permission = {"owner": owner_permission, "other": other_permission}[
            permission_fixture
        ]
        app_label, codename = permission.value.split(".")
        perm_object = request.getfixturevalue(f"permission_{codename}")
        assert perm_object.content_type.app_label == app_label
        if client.user:
            client.user.user_permissions.add(perm_object)

    image_file, image_name = create_image()
    variables = {
        "id": graphene.Node.to_global_id(
            OWNER_TYPE_TO_GRAPHQL_TYPE[owner_type], media_owner.pk
        ),
        "alt": "",
        "image": image_name,
    }
    body = get_multipart_request_body(
        MEDIA_CREATE_MUTATION, variables, image_file, image_name
    )

    # when
    response = client.post_multipart(body)

    # then
    if is_allowed:
        content = get_graphql_content(response)
        assert content["data"]["mediaCreate"]["errors"] == []
        assert media_owner.media.count() == 1
        assert mock_media_created.call_count == 1
    else:
        assert_no_permission(response)
        content = get_graphql_content_from_response(response)
        assert content["data"]["mediaCreate"] is None
        assert ProductMedia.objects.exists() is False
        mock_media_created.assert_not_called()
