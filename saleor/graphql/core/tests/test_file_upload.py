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


def test_file_upload_by_staff(staff_api_client, site_settings, media_root):
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

    expected_path = "http://testserver/media/" + image_file._name
    assert not errors
    assert data["uploadedFile"]["contentType"] == "image/png"
    assert data["uploadedFile"]["url"] == expected_path
    assert default_storage.exists(image_file._name)


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

    expected_path = "http://testserver/media/" + image_file._name
    assert not errors
    assert data["uploadedFile"]["contentType"] == "image/png"
    assert data["uploadedFile"]["url"] == expected_path
    assert default_storage.exists(image_file._name)


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

    expected_path = "http://testserver/media/" + image_file._name
    assert not errors
    assert data["uploadedFile"]["contentType"] == "image/png"
    assert data["uploadedFile"]["url"] == expected_path
    assert default_storage.exists(image_file._name)


def test_file_upload_file_with_the_same_name_already_exists(
    staff_api_client, media_root
):
    """Ensure that when the file with the same name as uploaded file,
    already exists, the file name will be renamed and save as another file.
    """
    # given
    image_file1, image_name1 = create_image()
    path = default_storage.save(image_file1._name, image_file1)

    image_file, image_name = create_image()
    assert image_file1 != image_file
    assert image_name == image_name1
    assert image_file._name == image_file1._name

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

    assert not errors
    assert data["uploadedFile"]["contentType"] == "image/png"
    file_url = data["uploadedFile"]["url"]
    assert file_url != "http://testserver/media/" + image_file._name
    assert file_url != "http://testserver/media/" + path
    assert default_storage.exists(file_url.replace("http://testserver/media/", ""))
