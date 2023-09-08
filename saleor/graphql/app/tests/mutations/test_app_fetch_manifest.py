import base64
from io import BytesIO
from unittest.mock import ANY, Mock

import pytest
import requests
from PIL import Image
from requests_hardened import HTTPSession

from ..... import schema_version
from .....app.error_codes import AppErrorCode
from .....thumbnail import IconThumbnailFormat
from ....tests.utils import assert_no_permission, get_graphql_content
from ...enums import AppExtensionMountEnum, AppExtensionTargetEnum
from ...mutations.app_fetch_manifest import FETCH_BRAND_DATA_TIMEOUT

APP_FETCH_MANIFEST_MUTATION = """
mutation AppFetchManifest(
  $manifest_url: String!
  $size: Int
  $format: IconThumbnailFormatEnum
) {
  appFetchManifest(manifestUrl:$manifest_url){
    manifest{
      identifier
      version
      about
      name
      appUrl
      configurationUrl
      tokenTargetUrl
      dataPrivacy
      dataPrivacyUrl
      homepageUrl
      supportUrl
      permissions{
        code
      }
      audience
      requiredSaleorVersion{
        constraint
        satisfied
      }
      author
      extensions{
        label
        url
        mount
        target
        permissions{
          code
          name
        }
      }
      brand{
        logo{
          default(size: $size, format: $format)
        }
      }
    }
    errors{
      field
      message
      code
    }
  }
}
"""


@pytest.mark.vcr
def test_app_fetch_manifest(staff_api_client, staff_user, permission_manage_apps):
    manifest_url = "http://localhost:3000/manifest"
    query = APP_FETCH_MANIFEST_MUTATION
    variables = {
        "manifest_url": manifest_url,
    }
    staff_user.user_permissions.set([permission_manage_apps])
    response = staff_api_client.post_graphql(
        query,
        variables=variables,
    )
    content = get_graphql_content(response)
    errors = content["data"]["appFetchManifest"]["errors"]
    manifest = content["data"]["appFetchManifest"]["manifest"]
    assert not errors
    assert manifest["identifier"] == "app2"
    assert manifest["version"] == "1.0.0"
    assert manifest["about"] == "Lorem ipsum"
    assert manifest["name"] == "app"
    assert manifest["appUrl"] == "http://localhost:8888/app"
    assert manifest["configurationUrl"] == "http://localhost:8888/configuration"
    assert manifest["tokenTargetUrl"] == "http://localhost:3000/register"
    assert manifest["dataPrivacy"] == "Lorem ipsum"
    assert manifest["dataPrivacyUrl"] == "http://localhost:8888/app-data-privacy"
    assert manifest["homepageUrl"] == "http://localhost:8888/homepage"
    assert manifest["supportUrl"] == "http://localhost:8888/support"
    assert set([perm["code"] for perm in manifest["permissions"]]) == {
        "MANAGE_ORDERS",
        "MANAGE_USERS",
    }
    assert manifest["requiredSaleorVersion"] is None
    assert manifest["brand"] is None


def test_app_fetch_manifest_custom_saleor_headers(
    app_manifest, monkeypatch, staff_api_client, permission_manage_apps
):
    # given
    mocked_get = Mock(return_value=Mock())
    mocked_get.return_value.json = Mock(return_value=app_manifest)

    monkeypatch.setattr(HTTPSession, "request", mocked_get)
    query = APP_FETCH_MANIFEST_MUTATION
    manifest_url = "http://localhost:3000/configuration/manifest"
    variables = {"manifest_url": manifest_url}

    # when
    staff_api_client.post_graphql(
        query, variables=variables, permissions=[permission_manage_apps]
    )

    # then
    mocked_get.assert_called_once_with(
        "GET",
        manifest_url,
        headers={"Saleor-Schema-Version": schema_version},
        timeout=ANY,
        allow_redirects=False,
    )


@pytest.mark.vcr
def test_app_fetch_manifest_with_audience(
    staff_api_client, staff_user, permission_manage_apps
):
    manifest_url = "http://localhost:3000/manifest"
    query = APP_FETCH_MANIFEST_MUTATION
    variables = {
        "manifest_url": manifest_url,
    }
    staff_user.user_permissions.set([permission_manage_apps])
    response = staff_api_client.post_graphql(
        query,
        variables=variables,
    )
    content = get_graphql_content(response)
    errors = content["data"]["appFetchManifest"]["errors"]
    manifest = content["data"]["appFetchManifest"]["manifest"]
    assert not errors
    assert manifest["audience"] == "http://localhost:8888/app"


def test_app_fetch_manifest_missing_permission(staff_api_client, staff_user):
    manifest_url = "http://localhost:3000/manifest"
    query = APP_FETCH_MANIFEST_MUTATION
    variables = {
        "manifest_url": manifest_url,
    }
    response = staff_api_client.post_graphql(
        query,
        variables=variables,
    )
    assert_no_permission(response)


@pytest.mark.vcr
def test_app_fetch_manifest_incorrect_permission_in_manifest(
    staff_user, staff_api_client, permission_manage_apps
):
    manifest_url = "http://localhost:3000/manifest-with-wrong-perm"
    query = APP_FETCH_MANIFEST_MUTATION
    variables = {
        "manifest_url": manifest_url,
    }
    staff_user.user_permissions.set([permission_manage_apps])
    response = staff_api_client.post_graphql(
        query,
        variables=variables,
    )
    content = get_graphql_content(response)
    errors = content["data"]["appFetchManifest"]["errors"]
    manifest = content["data"]["appFetchManifest"]["manifest"]
    assert len(errors) == 1
    assert errors[0] == {
        "field": "permissions",
        "message": "Given permissions don't exist.",
        "code": "INVALID_PERMISSION",
    }
    assert not manifest


@pytest.mark.vcr
def test_app_fetch_manifest_unable_to_connect(
    staff_user, staff_api_client, permission_manage_apps
):
    manifest_url = "http://localhost:3000/manifest-doesnt-exist"
    query = APP_FETCH_MANIFEST_MUTATION
    variables = {
        "manifest_url": manifest_url,
    }
    staff_user.user_permissions.set([permission_manage_apps])
    response = staff_api_client.post_graphql(
        query,
        variables=variables,
    )
    content = get_graphql_content(response)
    errors = content["data"]["appFetchManifest"]["errors"]

    assert len(errors) == 1
    assert errors[0] == {
        "field": "manifestUrl",
        "message": "Unable to fetch manifest data.",
        "code": "MANIFEST_URL_CANT_CONNECT",
    }


def test_app_fetch_manifest_timeout(
    staff_user, staff_api_client, permission_manage_apps, monkeypatch
):
    mocked_request = Mock()
    mocked_request.side_effect = requests.Timeout()
    monkeypatch.setattr(HTTPSession, "request", mocked_request)
    manifest_url = "http://localhost:3000/manifest-doesnt-exist"
    query = APP_FETCH_MANIFEST_MUTATION
    variables = {
        "manifest_url": manifest_url,
    }
    staff_user.user_permissions.set([permission_manage_apps])
    response = staff_api_client.post_graphql(
        query,
        variables=variables,
    )
    content = get_graphql_content(response)
    errors = content["data"]["appFetchManifest"]["errors"]

    assert len(errors) == 1
    assert errors[0] == {
        "field": "manifestUrl",
        "message": "The request to fetch manifest data timed out.",
        "code": "MANIFEST_URL_CANT_CONNECT",
    }


@pytest.mark.vcr
def test_app_fetch_manifest_wrong_format_of_response(
    staff_user, staff_api_client, permission_manage_apps
):
    manifest_url = "http://localhost:3000/manifest-wrong-format"
    query = APP_FETCH_MANIFEST_MUTATION
    variables = {
        "manifest_url": manifest_url,
    }
    staff_user.user_permissions.set([permission_manage_apps])
    response = staff_api_client.post_graphql(
        query,
        variables=variables,
    )
    content = get_graphql_content(response)
    errors = content["data"]["appFetchManifest"]["errors"]

    assert len(errors) == 1
    assert errors[0] == {
        "field": "manifestUrl",
        "message": "Incorrect structure of manifest.",
        "code": "INVALID_MANIFEST_FORMAT",
    }


def test_app_fetch_manifest_handle_exception(
    staff_user, staff_api_client, permission_manage_apps, monkeypatch
):
    mocked_get = Mock()
    mocked_get.side_effect = Exception()

    monkeypatch.setattr(HTTPSession, "request", mocked_get)
    manifest_url = "http://localhost:3000/manifest-wrong-format"
    query = APP_FETCH_MANIFEST_MUTATION
    variables = {
        "manifest_url": manifest_url,
    }
    staff_user.user_permissions.set([permission_manage_apps])
    response = staff_api_client.post_graphql(
        query,
        variables=variables,
    )
    content = get_graphql_content(response)
    errors = content["data"]["appFetchManifest"]["errors"]

    assert len(errors) == 1
    assert errors[0] == {
        "code": "INVALID",
        "field": "manifestUrl",
        "message": "Can't fetch manifest data. Please try later.",
    }


@pytest.mark.parametrize(
    "missing_field",
    [
        "id",
        "version",
        "name",
    ],
)
def test_app_fetch_manifest_missing_fields(
    missing_field, app_manifest, monkeypatch, staff_api_client, permission_manage_apps
):
    # given
    del app_manifest[missing_field]
    mocked_get_response = Mock()
    mocked_get_response.json.return_value = app_manifest

    monkeypatch.setattr(HTTPSession, "request", Mock(return_value=mocked_get_response))
    query = APP_FETCH_MANIFEST_MUTATION
    manifest_url = "http://localhost:3000/configuration/manifest"
    variables = {
        "manifest_url": manifest_url,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=[permission_manage_apps]
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["appFetchManifest"]["errors"]

    assert len(errors) == 1
    assert errors[0] == {
        "code": "REQUIRED",
        "field": missing_field,
        "message": "Field required.",
    }


@pytest.mark.parametrize(
    "missing_field",
    [
        "label",
        "url",
        "mount",
    ],
)
def test_app_fetch_manifest_missing_extension_fields(
    missing_field, app_manifest, monkeypatch, staff_api_client, permission_manage_apps
):
    # given
    app_manifest["extensions"] = [
        {
            "permissions": ["MANAGE_PRODUCTS"],
            "label": "Create product with App",
            "url": "http://127.0.0.1:9090/app-extension",
            "mount": AppExtensionMountEnum.PRODUCT_OVERVIEW_CREATE.name,
        }
    ]
    del app_manifest["extensions"][0][missing_field]
    mocked_get_response = Mock()
    mocked_get_response.json.return_value = app_manifest

    monkeypatch.setattr(HTTPSession, "request", Mock(return_value=mocked_get_response))
    query = APP_FETCH_MANIFEST_MUTATION
    manifest_url = "http://localhost:3000/configuration/manifest"
    variables = {
        "manifest_url": manifest_url,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=[permission_manage_apps]
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["appFetchManifest"]["errors"]

    assert len(errors) == 1
    assert errors[0] == {
        "code": "REQUIRED",
        "field": "extensions",
        "message": f"Missing required fields for app extension: {missing_field}.",
    }


@pytest.mark.parametrize(
    "incorrect_field",
    ["target", "mount"],
)
def test_app_fetch_manifest_extensions_incorrect_enum_values(
    incorrect_field, app_manifest, monkeypatch, staff_api_client, permission_manage_apps
):
    # given
    app_manifest["extensions"] = [
        {
            "permissions": ["MANAGE_PRODUCTS"],
            "label": "Create product with App",
            "url": "http://127.0.0.1:9090/app-extension",
            "mount": AppExtensionMountEnum.PRODUCT_OVERVIEW_CREATE.name,
        }
    ]
    app_manifest["extensions"][0][incorrect_field] = "INCORRECT_VALUE"

    mocked_get_response = Mock()
    mocked_get_response.json.return_value = app_manifest

    monkeypatch.setattr(HTTPSession, "request", Mock(return_value=mocked_get_response))
    query = APP_FETCH_MANIFEST_MUTATION
    manifest_url = "http://localhost:3000/configuration/manifest"
    variables = {
        "manifest_url": manifest_url,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=[permission_manage_apps]
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["appFetchManifest"]["errors"]

    assert len(errors) == 1
    expected_errors = [
        {
            "code": "INVALID",
            "field": "extensions",
            "message": f"Incorrect value for field: {incorrect_field}",
        },
    ]

    assert errors == expected_errors


@pytest.mark.parametrize(
    "url, target, app_url",
    [
        ("/app", AppExtensionTargetEnum.APP_PAGE.name, ""),
        ("/app", AppExtensionTargetEnum.APP_PAGE.name, "https://www.example.com/app"),
        ("/app", AppExtensionTargetEnum.POPUP.name, "https://www.example.com/app"),
    ],
)
def test_app_fetch_manifest_extensions_correct_url(
    url,
    target,
    app_url,
    app_manifest,
    monkeypatch,
    staff_api_client,
    permission_manage_apps,
):
    # given
    app_manifest["appUrl"] = app_url
    app_manifest["extensions"] = [
        {
            "permissions": ["MANAGE_PRODUCTS"],
            "label": "Create product with App",
            "url": url,
            "mount": AppExtensionMountEnum.PRODUCT_OVERVIEW_CREATE.name,
            "target": target,
        }
    ]

    mocked_get_response = Mock()
    mocked_get_response.json.return_value = app_manifest

    monkeypatch.setattr(HTTPSession, "request", Mock(return_value=mocked_get_response))
    query = APP_FETCH_MANIFEST_MUTATION
    manifest_url = "http://localhost:3000/configuration/manifest"
    variables = {
        "manifest_url": manifest_url,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=[permission_manage_apps]
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["appFetchManifest"]["errors"]
    assert len(errors) == 0


@pytest.mark.parametrize(
    "url, target",
    [
        ("http:/127.0.0.1:8080/app", AppExtensionTargetEnum.POPUP.name),
        ("127.0.0.1:8080/app", AppExtensionTargetEnum.POPUP.name),
        ("", AppExtensionTargetEnum.POPUP.name),
        ("/app", AppExtensionTargetEnum.POPUP.name),
        ("www.example.com/app", AppExtensionTargetEnum.POPUP.name),
        ("https://www.example.com/app", AppExtensionTargetEnum.APP_PAGE.name),
        ("http://www.example.com/app", AppExtensionTargetEnum.APP_PAGE.name),
    ],
)
def test_app_fetch_manifest_extensions_incorrect_url(
    url, target, app_manifest, monkeypatch, staff_api_client, permission_manage_apps
):
    # given
    app_manifest["extensions"] = [
        {
            "permissions": ["MANAGE_PRODUCTS"],
            "label": "Create product with App",
            "url": url,
            "mount": AppExtensionMountEnum.PRODUCT_OVERVIEW_CREATE.name,
            "target": target,
        }
    ]

    mocked_get_response = Mock()
    mocked_get_response.json.return_value = app_manifest

    monkeypatch.setattr(HTTPSession, "request", Mock(return_value=mocked_get_response))
    query = APP_FETCH_MANIFEST_MUTATION
    manifest_url = "http://localhost:3000/configuration/manifest"
    variables = {
        "manifest_url": manifest_url,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=[permission_manage_apps]
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["appFetchManifest"]["errors"]

    assert len(errors) == 1
    assert errors[0] == {
        "code": "INVALID_URL_FORMAT",
        "field": "extensions",
        "message": "Incorrect value for field: url.",
    }


@pytest.mark.parametrize(
    "app_permissions, extension_permissions",
    [
        ([], ["MANAGE_PRODUCTS"]),
        (["MANAGE_PRODUCTS"], ["MANAGE_PRODUCTS", "MANAGE_APPS"]),
    ],
)
def test_app_fetch_manifest_extensions_permission_out_of_scope(
    app_permissions,
    extension_permissions,
    app_manifest,
    monkeypatch,
    staff_api_client,
    permission_manage_apps,
):
    # given
    app_manifest["permissions"] = app_permissions
    app_manifest["extensions"] = [
        {
            "permissions": extension_permissions,
            "label": "Create product with App",
            "url": "http://127.0.0.1:8080/app",
            "mount": AppExtensionMountEnum.PRODUCT_OVERVIEW_CREATE.name,
        }
    ]

    mocked_get_response = Mock()
    mocked_get_response.json.return_value = app_manifest

    monkeypatch.setattr(HTTPSession, "request", Mock(return_value=mocked_get_response))
    query = APP_FETCH_MANIFEST_MUTATION
    manifest_url = "http://localhost:3000/configuration/manifest"
    variables = {
        "manifest_url": manifest_url,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=[permission_manage_apps]
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["appFetchManifest"]["errors"]

    assert len(errors) == 1
    assert errors[0] == {
        "code": "OUT_OF_SCOPE_PERMISSION",
        "field": "extensions",
        "message": "Extension permission must be listed in App's permissions.",
    }


def test_app_fetch_manifest_extensions_invalid_permission(
    app_manifest, monkeypatch, staff_api_client, permission_manage_apps
):
    # given
    app_manifest["permissions"] = ["MANAGE_ORDERS"]
    app_manifest["extensions"] = [
        {
            "permissions": ["incorrect_permission"],
            "label": "Create product with App",
            "url": "http://127.0.0.1:8080/app",
            "mount": AppExtensionMountEnum.PRODUCT_OVERVIEW_CREATE.name,
        }
    ]

    mocked_get_response = Mock()
    mocked_get_response.json.return_value = app_manifest

    monkeypatch.setattr(HTTPSession, "request", Mock(return_value=mocked_get_response))
    query = APP_FETCH_MANIFEST_MUTATION
    manifest_url = "http://localhost:3000/configuration/manifest"
    variables = {
        "manifest_url": manifest_url,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=[permission_manage_apps]
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["appFetchManifest"]["errors"]

    assert len(errors) == 1
    assert errors[0] == {
        "code": "INVALID_PERMISSION",
        "field": "extensions",
        "message": "Given permissions don't exist.",
    }


def test_app_fetch_manifest_with_extensions(
    staff_api_client, staff_user, app_manifest, permission_manage_apps, monkeypatch
):
    # given
    manifest_url = "http://localhost:3000/manifest"

    app_manifest["extensions"] = [
        {
            "permissions": ["MANAGE_PRODUCTS"],
            "label": "Create product with App",
            "url": "http://127.0.0.1:8080/app",
            "mount": AppExtensionMountEnum.PRODUCT_OVERVIEW_CREATE.name,
        }
    ]

    mocked_get_response = Mock()
    mocked_get_response.json.return_value = app_manifest

    monkeypatch.setattr(HTTPSession, "request", Mock(return_value=mocked_get_response))

    query = APP_FETCH_MANIFEST_MUTATION
    variables = {
        "manifest_url": manifest_url,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=[permission_manage_apps]
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["appFetchManifest"]["errors"]
    manifest = content["data"]["appFetchManifest"]["manifest"]
    extensions = manifest["extensions"]

    assert not errors
    assert len(extensions) == 1

    extension = extensions[0]
    assert extension["permissions"] == [
        {"code": "MANAGE_PRODUCTS", "name": "Manage products."}
    ]
    assert extension["label"] == "Create product with App"
    assert extension["url"] == "http://127.0.0.1:8080/app"
    assert extension["mount"] == AppExtensionMountEnum.PRODUCT_OVERVIEW_CREATE.name
    assert extension["target"] == AppExtensionTargetEnum.POPUP.name


def test_app_fetch_manifest_with_required_saleor_version(
    staff_api_client, app_manifest, permission_manage_apps, monkeypatch
):
    # given
    required_saleor_version = "<3.11"
    app_manifest["requiredSaleorVersion"] = required_saleor_version
    mocked_get_response = Mock()
    mocked_get_response.json.return_value = app_manifest
    monkeypatch.setattr(HTTPSession, "request", Mock(return_value=mocked_get_response))

    # when
    response = staff_api_client.post_graphql(
        APP_FETCH_MANIFEST_MUTATION,
        variables={"manifest_url": "http://localhost:3000/manifest"},
        permissions=[permission_manage_apps],
    )

    # then
    content = get_graphql_content(response)
    manifest = content["data"]["appFetchManifest"]["manifest"]
    assert len(content["data"]["appFetchManifest"]["errors"]) == 0
    assert manifest["requiredSaleorVersion"] == {
        "constraint": required_saleor_version,
        "satisfied": False,
    }


def test_app_fetch_manifest_with_invalid_required_saleor_version(
    staff_api_client, app_manifest, permission_manage_apps, monkeypatch
):
    # given
    required_saleor_version = "3.wrong.1"
    app_manifest["requiredSaleorVersion"] = required_saleor_version
    mocked_get_response = Mock()
    mocked_get_response.json.return_value = app_manifest
    monkeypatch.setattr(HTTPSession, "request", Mock(return_value=mocked_get_response))

    # when
    response = staff_api_client.post_graphql(
        APP_FETCH_MANIFEST_MUTATION,
        variables={"manifest_url": "http://localhost:3000/manifest"},
        permissions=[permission_manage_apps],
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["appFetchManifest"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "requiredSaleorVersion"
    assert errors[0]["code"] == AppErrorCode.INVALID.name


def test_app_fetch_manifest_with_author(
    staff_api_client, app_manifest, permission_manage_apps, monkeypatch
):
    # given
    app_manifest["author"] = "Acme Ltd"
    mocked_get_response = Mock()
    mocked_get_response.json.return_value = app_manifest
    monkeypatch.setattr(HTTPSession, "request", Mock(return_value=mocked_get_response))

    # when
    response = staff_api_client.post_graphql(
        APP_FETCH_MANIFEST_MUTATION,
        variables={"manifest_url": "http://localhost:3000/manifest"},
        permissions=[permission_manage_apps],
    )

    # then
    content = get_graphql_content(response)
    manifest = content["data"]["appFetchManifest"]["manifest"]
    assert len(content["data"]["appFetchManifest"]["errors"]) == 0
    assert manifest["author"] == app_manifest["author"]


def test_app_fetch_manifest_with_empty_author(
    staff_api_client, app_manifest, permission_manage_apps, monkeypatch
):
    # given
    app_manifest["author"] = " "
    mocked_get_response = Mock()
    mocked_get_response.json.return_value = app_manifest
    monkeypatch.setattr(HTTPSession, "request", Mock(return_value=mocked_get_response))

    # when
    response = staff_api_client.post_graphql(
        APP_FETCH_MANIFEST_MUTATION,
        variables={"manifest_url": "http://localhost:3000/manifest"},
        permissions=[permission_manage_apps],
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["appFetchManifest"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "author"
    assert errors[0]["code"] == AppErrorCode.INVALID.name


@pytest.mark.parametrize(
    "format,expected_format,size",
    [
        (None, "png", None),
        (IconThumbnailFormat.WEBP, "webp", 120),
        (IconThumbnailFormat.ORIGINAL, "png", 0),
    ],
)
def test_app_fetch_manifest_with_brand_data(
    format,
    expected_format,
    size,
    staff_api_client,
    app_manifest,
    permission_manage_apps,
    icon_image,
    monkeypatch,
):
    # given
    logo_url = "http://localhost:3000/logo.png"
    app_manifest["brand"] = {"logo": {"default": logo_url}}
    mocked_get_response = Mock()
    mocked_get_response.json.return_value = app_manifest
    monkeypatch.setattr(HTTPSession, "request", Mock(return_value=mocked_get_response))
    mock_fetch_icon_image = Mock(return_value=icon_image)
    monkeypatch.setattr(
        "saleor.app.installation_utils.fetch_icon_image", mock_fetch_icon_image
    )

    # when
    response = staff_api_client.post_graphql(
        APP_FETCH_MANIFEST_MUTATION,
        variables={
            "manifest_url": "http://localhost:3000/manifest",
            "size": size,
            "format": format.upper() if format else None,
        },
        permissions=[permission_manage_apps],
    )

    # then
    mock_fetch_icon_image.assert_called_once_with(
        logo_url, timeout=FETCH_BRAND_DATA_TIMEOUT
    )
    content = get_graphql_content(response)
    manifest = content["data"]["appFetchManifest"]["manifest"]
    assert len(content["data"]["appFetchManifest"]["errors"]) == 0
    # decode and check icon thumbnail from data url
    data_url_prefix, base64_icon = manifest["brand"]["logo"]["default"].split(",", 1)
    assert data_url_prefix == f"data:image/{expected_format};base64"
    icon_thumbnail = BytesIO(base64.b64decode(base64_icon.encode()))
    with Image.open(icon_thumbnail) as image:
        assert image.format == expected_format.upper()


def test_app_fetch_manifest_with_invalid_brand_data(
    staff_api_client, app_manifest, permission_manage_apps, monkeypatch
):
    # given
    app_manifest["brand"] = {"logo": {"default": "wrong-url.png"}}
    mocked_get_response = Mock()
    mocked_get_response.json.return_value = app_manifest
    monkeypatch.setattr(HTTPSession, "request", Mock(return_value=mocked_get_response))

    # when
    response = staff_api_client.post_graphql(
        APP_FETCH_MANIFEST_MUTATION,
        variables={"manifest_url": "http://localhost:3000/manifest"},
        permissions=[permission_manage_apps],
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["appFetchManifest"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "brand"
    assert errors[0]["code"] == AppErrorCode.INVALID_URL_FORMAT.name
