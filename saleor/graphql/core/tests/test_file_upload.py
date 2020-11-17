from django.core.files.storage import default_storage

from ....product.tests.utils import create_image
from ...tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_multipart_request_body,
)

FILE_UPLOAD_MUTATION = """
mutation fileUpload($file: Upload!) {
    fileUpload(file: $file) {
        uploadedFile {
            url
            contentType
        }
        uploadErrors {
            code
        }
    }
}
"""


def test_file_upload_by_staff(staff_api_client, media_root):
    # given
    image_file, image_name = create_image()
    variables = {"image": image_name}
    body = get_multipart_request_body(
        FILE_UPLOAD_MUTATION, variables, image_file, image_name
    )

    # when
    response = staff_api_client.post_multipart(body)

    # then
    content = get_graphql_content(response)
    data = content["data"]["fileUpload"]
    errors = data["uploadErrors"]

    expected_path = image_file._name
    assert not errors
    assert data["uploadedFile"]["contentType"] == "image/png"
    assert data["uploadedFile"]["url"] == expected_path
    assert default_storage.exists(expected_path)


def test_file_upload_by_customer(user_api_client, media_root):
    # given
    image_file, image_name = create_image()
    variables = {"image": image_name}
    body = get_multipart_request_body(
        FILE_UPLOAD_MUTATION, variables, image_file, image_name
    )

    # when
    response = user_api_client.post_multipart(body)

    # then
    assert_no_permission(response)


def test_file_upload_by_app(app_api_client, media_root):
    # given
    image_file, image_name = create_image()
    variables = {"image": image_name}
    body = get_multipart_request_body(
        FILE_UPLOAD_MUTATION, variables, image_file, image_name
    )

    # when
    response = app_api_client.post_multipart(body)

    # then
    content = get_graphql_content(response)
    data = content["data"]["fileUpload"]
    errors = data["uploadErrors"]

    expected_path = image_file._name
    assert not errors
    assert data["uploadedFile"]["contentType"] == "image/png"
    assert data["uploadedFile"]["url"] == expected_path
    assert default_storage.exists(expected_path)


def test_file_upload_by_superuser(superuser_api_client, media_root):
    # given
    image_file, image_name = create_image()
    variables = {"image": image_name}
    body = get_multipart_request_body(
        FILE_UPLOAD_MUTATION, variables, image_file, image_name
    )

    # when
    response = superuser_api_client.post_multipart(body)

    # then
    content = get_graphql_content(response)
    data = content["data"]["fileUpload"]
    errors = data["uploadErrors"]

    expected_path = image_file._name
    assert not errors
    assert data["uploadedFile"]["contentType"] == "image/png"
    assert data["uploadedFile"]["url"] == expected_path
    assert default_storage.exists(expected_path)
