import os
from unittest.mock import patch
from urllib.parse import urlparse

from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile

from ....core.error_codes import UploadErrorCode
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
            field
        }
    }
}
"""


@patch("saleor.graphql.core.validators.file.magic.from_buffer")
def test_file_upload_by_staff(
    from_buffer_mock, staff_api_client, site_settings, media_root
):
    # given
    from_buffer_mock.return_value = "image/jpeg"
    image_file, image_name = create_image()
    variables = {"file": image_name}
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


@patch("saleor.graphql.core.validators.file.magic.from_buffer")
def test_file_upload_by_customer(from_buffer_mock, user_api_client, media_root):
    # given
    from_buffer_mock.return_value = "image/jpeg"
    image_file, image_name = create_image()
    variables = {"file": image_name}
    body = get_multipart_request_body(
        FILE_UPLOAD_MUTATION, variables, image_file, image_name
    )

    # when
    response = user_api_client.post_multipart(body)

    # then
    assert_no_permission(response)


@patch("saleor.graphql.core.validators.file.magic.from_buffer")
def test_file_upload_by_app(from_buffer_mock, app_api_client, media_root):
    # given
    from_buffer_mock.return_value = "image/jpeg"
    image_file, image_name = create_image()
    variables = {"file": image_name}
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


@patch("saleor.graphql.core.validators.file.magic.from_buffer")
def test_file_upload_by_superuser(from_buffer_mock, superuser_api_client, media_root):
    # given
    from_buffer_mock.return_value = "image/jpeg"
    image_file, image_name = create_image()
    variables = {"file": image_name}
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


@patch("saleor.graphql.core.validators.file.magic.from_buffer")
def test_file_upload_file_with_the_same_name_already_exists(
    from_buffer_mock, staff_api_client, media_root, site_settings
):
    # given
    from_buffer_mock.return_value = "image/jpeg"
    image_file1, image_name1 = create_image()
    path = default_storage.save(image_file1._name, image_file1)

    image_file, image_name = create_image()
    assert image_file1 != image_file
    assert image_name == image_name1
    assert image_file._name == image_file1._name

    variables = {"file": image_name}
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


@patch("saleor.graphql.core.validators.file.magic.from_buffer")
def test_file_upload_file_name_with_space(
    from_buffer_mock, staff_api_client, media_root
):
    # given
    from_buffer_mock.return_value = "image/jpeg"
    image_file, image_name = create_image("file name with spaces")
    variables = {"file": image_name}
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


@patch("saleor.graphql.core.validators.file.magic.from_buffer")
def test_file_upload_file_name_with_encoded_value(
    from_buffer_mock, staff_api_client, media_root
):
    # given
    from_buffer_mock.return_value = "image/jpeg"
    image_file, image_name = create_image("file%20name")
    variables = {"file": image_name}
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


@patch("saleor.graphql.core.validators.file.magic.from_buffer")
def test_file_upload_invalid_mime_type(from_buffer_mock, staff_api_client, media_root):
    # given
    from_buffer_mock.return_value = "application/x-msdownload"
    exe_file = SimpleUploadedFile(
        "malicious.exe",
        b"fake executable content",
        content_type="application/x-msdownload",
    )
    variables = {"file": "malicious.exe"}
    body = get_multipart_request_body(
        FILE_UPLOAD_MUTATION, variables, exe_file, "malicious.exe"
    )

    # when
    response = staff_api_client.post_multipart(body)

    # then
    content = get_graphql_content(response)
    data = content["data"]["fileUpload"]
    errors = data["errors"]

    assert errors
    assert len(errors) == 1
    assert errors[0]["code"] == UploadErrorCode.UNSUPPORTED_MIME_TYPE.name
    assert errors[0]["field"] == "file"


@patch("saleor.graphql.core.validators.file.magic.from_buffer")
def test_file_upload_invalid_extension(from_buffer_mock, staff_api_client, media_root):
    # given
    from_buffer_mock.return_value = "image/jpeg"
    exe_file = SimpleUploadedFile(
        "test.png", b"fake jpeg content", content_type="image/jpeg"
    )
    variables = {"file": "test.png"}
    body = get_multipart_request_body(
        FILE_UPLOAD_MUTATION, variables, exe_file, "test.png"
    )

    # when
    response = staff_api_client.post_multipart(body)

    # then
    content = get_graphql_content(response)
    data = content["data"]["fileUpload"]
    errors = data["errors"]

    assert errors
    assert len(errors) == 1
    assert errors[0]["code"] == UploadErrorCode.INVALID_FILE_TYPE.name
    assert errors[0]["field"] == "file"
