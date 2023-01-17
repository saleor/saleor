import os
from urllib.parse import urlparse

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
        errors {
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
    errors = data["errors"]

    assert not errors
    assert data["uploadedFile"]["contentType"] == "image/jpeg"
    file_name, format = os.path.splitext(image_file._name)
    returned_url = data["uploadedFile"]["url"]
    file_path = urlparse(returned_url).path
    assert file_path.startswith(f"/media/file_upload/{file_name}")
    assert file_path.endswith(format)
    assert default_storage.exists(file_path.lstrip("/media"))


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
    errors = data["errors"]

    assert not errors
    assert data["uploadedFile"]["contentType"] == "image/jpeg"
    file_name, format = os.path.splitext(image_file._name)
    returned_url = data["uploadedFile"]["url"]
    file_path = urlparse(returned_url).path
    assert file_path.startswith(f"/media/file_upload/{file_name}")
    assert file_path.endswith(format)
    assert default_storage.exists(file_path.lstrip("/media"))


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
    errors = data["errors"]

    assert not errors
    assert data["uploadedFile"]["contentType"] == "image/jpeg"
    file_name, format = os.path.splitext(image_file._name)
    returned_url = data["uploadedFile"]["url"]
    file_path = urlparse(returned_url).path
    assert file_path.startswith(f"/media/file_upload/{file_name}")
    assert file_path.endswith(format)
    assert default_storage.exists(file_path.lstrip("/media"))


def test_file_upload_file_with_the_same_name_already_exists(
    staff_api_client, media_root, site_settings
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
    errors = data["errors"]

    domain = site_settings.site.domain
    assert not errors
    assert data["uploadedFile"]["contentType"] == "image/jpeg"
    file_url = data["uploadedFile"]["url"]
    assert file_url != f"http://{domain}/media/{image_file._name}"
    assert file_url != f"http://{domain}/media/{path}"
    assert default_storage.exists(file_url.replace(f"http://{domain}/media/", ""))


def test_file_upload_file_name_with_space(staff_api_client, media_root):
    # given
    image_file, image_name = create_image("file name with spaces")
    variables = {"image": image_name}
    body = get_multipart_request_body(
        FILE_UPLOAD_MUTATION, variables, image_file, image_name
    )

    # when
    response = staff_api_client.post_multipart(body)

    # then
    content = get_graphql_content(response)
    data = content["data"]["fileUpload"]
    errors = data["errors"]

    assert not errors
    assert data["uploadedFile"]["contentType"] == "image/jpeg"
    file_name, format = os.path.splitext(image_file._name)
    file_name = file_name.replace(" ", "_")
    returned_url = data["uploadedFile"]["url"]
    file_path = urlparse(returned_url).path
    assert file_path.startswith(f"/media/file_upload/{file_name}")
    assert file_path.endswith(format)
    assert default_storage.exists(file_path.lstrip("/media"))


def test_file_upload_file_name_with_encoded_value(staff_api_client, media_root):
    # given
    image_file, image_name = create_image("file%20name")
    variables = {"image": image_name}
    body = get_multipart_request_body(
        FILE_UPLOAD_MUTATION, variables, image_file, image_name
    )

    # when
    response = staff_api_client.post_multipart(body)

    # then
    content = get_graphql_content(response)
    data = content["data"]["fileUpload"]
    errors = data["errors"]

    assert not errors
    assert data["uploadedFile"]["contentType"] == "image/jpeg"
    file_name, format = os.path.splitext(image_file._name)
    returned_url = data["uploadedFile"]["url"]
    file_path = urlparse(returned_url).path
    assert file_path.startswith(f"/media/file_upload/{file_name}")
    assert file_path.endswith(format)
    assert default_storage.exists(file_path.lstrip("/media"))
