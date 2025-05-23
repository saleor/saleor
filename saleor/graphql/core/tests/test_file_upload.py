import os
from urllib.parse import urlparse

from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile

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
MALICIOUS_SVG = b"""
<svg xmlns="http://www.w3.org/2000/svg">
  <script>alert("XSS")</script>
  <circle cx="50" cy="50" r="40" />
</svg>
"""

SAFE_SVG = b"""
<svg xmlns="http://www.w3.org/2000/svg">
  <circle cx="10" cy="10" r="5" />
</svg>
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


def test_file_upload_sanitizes_svg(staff_api_client, media_root):
    # Prepare malicious SVG file
    file_name = "malicious.svg"
    svg_file = SimpleUploadedFile(
        file_name, MALICIOUS_SVG, content_type="image/svg+xml"
    )
    variables = {"image": file_name}
    body = get_multipart_request_body(
        FILE_UPLOAD_MUTATION, variables, svg_file, file_name
    )

    # when
    response = staff_api_client.post_multipart(body)

    # Parse GraphQL response
    content = get_graphql_content(response)
    url = content["data"]["fileUpload"]["uploadedFile"]["url"]

    # Read the saved file and verify it's sanitized
    relative_path = urlparse(url).path.removeprefix("/media/")
    with default_storage.open(relative_path, "rb") as saved_file:
        saved_content = saved_file.read()
        assert b"<script>" not in saved_content
        assert b"alert" not in saved_content
        assert b"<circle" in saved_content


def test_file_upload_preserves_safe_svg(staff_api_client, media_root):
    # Upload a clean SVG with no malicious code
    file_name = "clean.svg"
    svg_file = SimpleUploadedFile(file_name, SAFE_SVG, content_type="image/svg+xml")
    variables = {"image": file_name}
    body = get_multipart_request_body(
        FILE_UPLOAD_MUTATION, variables, svg_file, file_name
    )

    # when
    response = staff_api_client.post_multipart(body)

    # Extract and check result
    content = get_graphql_content(response)
    data = content["data"]["fileUpload"]["uploadedFile"]
    assert data["contentType"] == "image/svg+xml"

    # Read the saved file and verify content is preserved
    relative_path = urlparse(data["url"]).path.removeprefix("/media/")
    with default_storage.open(relative_path, "rb") as saved_file:
        saved_content = saved_file.read()
        assert b"<circle" in saved_content
        assert b"<script" not in saved_content
        assert b"alert" not in saved_content
        assert b"onload" not in saved_content


def test_file_upload_jpeg_is_not_sanitized(staff_api_client, media_root):
    image_file, image_name = create_image()
    variables = {"image": image_name}
    body = get_multipart_request_body(
        FILE_UPLOAD_MUTATION, variables, image_file, image_name
    )

    response = staff_api_client.post_multipart(body)
    content = get_graphql_content(response)
    data = content["data"]["fileUpload"]

    assert data["uploadedFile"]["contentType"] == "image/jpeg"
    assert b"<script>" not in image_file.read()  # confirm this was never sanitized


def test_svg_upload_rejects_empty_file(staff_api_client, media_root):
    # Simulate an SVG file with no content
    empty_uploaded_file = SimpleUploadedFile(
        name="empty.svg", content=b"", content_type="image/svg+xml"
    )

    variables = {"image": "empty.svg"}
    body = get_multipart_request_body(
        FILE_UPLOAD_MUTATION, variables, empty_uploaded_file, "empty.svg"
    )

    response = staff_api_client.post_multipart(body)
    content = get_graphql_content(response, ignore_errors=True)

    # Expect a GraphQL error due to empty file
    assert "errors" in content
    assert "failed" in content["errors"][0]["message"].lower()
