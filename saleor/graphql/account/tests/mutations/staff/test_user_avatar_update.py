import os
from unittest.mock import MagicMock

from django.core.files import File

from ......account.error_codes import AccountErrorCode
from ......product.tests.utils import create_image
from ......thumbnail.models import Thumbnail
from .....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_multipart_request_body,
)

USER_AVATAR_UPDATE_MUTATION = """
    mutation userAvatarUpdate($image: Upload!) {
        userAvatarUpdate(image: $image) {
            user {
                avatar(size: 0) {
                    url
                }
            }
            accountErrors {
                field
                code
                message
            }
        }
    }
"""


def test_user_avatar_update_mutation_permission(api_client):
    """Should raise error if user is not staff."""

    query = USER_AVATAR_UPDATE_MUTATION

    image_file, image_name = create_image("avatar")
    variables = {"image": image_name}
    body = get_multipart_request_body(query, variables, image_file, image_name)
    response = api_client.post_multipart(body)

    assert_no_permission(response)


def test_user_avatar_update_mutation(monkeypatch, staff_api_client, media_root):
    query = USER_AVATAR_UPDATE_MUTATION

    user = staff_api_client.user

    image_file, image_name = create_image("avatar")
    variables = {"image": image_name}
    body = get_multipart_request_body(query, variables, image_file, image_name)

    # when
    response = staff_api_client.post_multipart(body)

    # then
    content = get_graphql_content(response)

    data = content["data"]["userAvatarUpdate"]
    user.refresh_from_db()

    assert user.avatar
    assert data["user"]["avatar"]["url"].startswith(
        "https://example.com/media/user-avatars/avatar"
    )
    img_name, format = os.path.splitext(image_file._name)
    file_name = user.avatar.name
    assert file_name != image_file._name
    assert file_name.startswith(f"user-avatars/{img_name}")
    assert file_name.endswith(format)


def test_user_avatar_update_mutation_image_exists(staff_api_client, media_root):
    query = USER_AVATAR_UPDATE_MUTATION

    user = staff_api_client.user
    avatar_mock = MagicMock(spec=File)
    avatar_mock.name = "image.jpg"
    user.avatar = avatar_mock
    user.save()

    # create thumbnail for old avatar
    Thumbnail.objects.create(user=staff_api_client.user, size=128)
    assert user.thumbnails.exists()

    image_file, image_name = create_image("new_image")
    variables = {"image": image_name}
    body = get_multipart_request_body(query, variables, image_file, image_name)

    # when
    response = staff_api_client.post_multipart(body)

    # then
    content = get_graphql_content(response)

    data = content["data"]["userAvatarUpdate"]
    user.refresh_from_db()

    assert user.avatar != avatar_mock
    assert data["user"]["avatar"]["url"].startswith(
        "https://example.com/media/user-avatars/new_image"
    )
    assert not user.thumbnails.exists()


def test_user_avatar_update_mutation_file_size_exceeds_limit(
    staff_api_client, media_root, settings
):
    # given
    settings.MAX_IMAGE_FILE_SIZE = 1
    image_file, image_name = create_image("avatar")
    variables = {"image": image_name}
    body = get_multipart_request_body(
        USER_AVATAR_UPDATE_MUTATION, variables, image_file, image_name
    )

    # when
    response = staff_api_client.post_multipart(body)
    content = get_graphql_content(response)

    # then
    errors = content["data"]["userAvatarUpdate"]["accountErrors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "image"
    assert errors[0]["code"] == AccountErrorCode.FILE_SIZE_LIMIT_EXCEEDED.name
    assert "File size exceeds the maximum allowed size" in errors[0]["message"]
    staff_api_client.user.refresh_from_db()
    assert not staff_api_client.user.avatar
