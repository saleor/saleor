import graphene
import pytest

from .....permission.enums import AccountPermissions
from .....thumbnail import IconThumbnailFormat
from .....thumbnail.models import Thumbnail
from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)

APPS_INSTALLATION_QUERY = """
    {
      appsInstallations{
        id
      }
    }
"""


def test_apps_installation(app_installation, staff_api_client, permission_manage_apps):
    response = staff_api_client.post_graphql(
        APPS_INSTALLATION_QUERY, permissions=[permission_manage_apps]
    )
    content = get_graphql_content(response)
    installations = content["data"]["appsInstallations"]

    assert len(installations) == 1
    _, app_id = graphene.Node.from_global_id(installations[0]["id"])
    assert int(app_id) == app_installation.id


def test_apps_installation_by_app(
    app_installation, app_api_client, permission_manage_apps
):
    response = app_api_client.post_graphql(
        APPS_INSTALLATION_QUERY, permissions=[permission_manage_apps]
    )
    content = get_graphql_content(response)
    installations = content["data"]["appsInstallations"]

    assert len(installations) == 1
    _, app_id = graphene.Node.from_global_id(installations[0]["id"])
    assert int(app_id) == app_installation.id


def test_apps_installation_by_app_missing_permission(app_api_client):
    response = app_api_client.post_graphql(APPS_INSTALLATION_QUERY)
    assert_no_permission(response)


def test_apps_installation_missing_permission(staff_api_client):
    response = staff_api_client.post_graphql(APPS_INSTALLATION_QUERY)
    assert_no_permission(response)


APPS_INSTALLATION_QUERY_WITH_INSTALLED_BY = """
    {
      appsInstallations{
        id
        installedBy {
          id
          email
        }
      }
    }
"""

MISSING_MANAGE_STAFF_MESSAGE = (
    "To access this path, you need one of the following permissions: "
    f"{AccountPermissions.MANAGE_STAFF.name}"
)


def test_apps_installation_installed_by(
    app_installation,
    staff_api_client,
    permission_manage_apps,
    permission_manage_staff,
    staff_user,
):
    # given
    app_installation.installed_by = staff_user
    app_installation.save(update_fields=["installed_by"])

    # when
    response = staff_api_client.post_graphql(
        APPS_INSTALLATION_QUERY_WITH_INSTALLED_BY,
        permissions=[permission_manage_apps, permission_manage_staff],
    )

    # then
    content = get_graphql_content(response)
    installations = content["data"]["appsInstallations"]
    assert len(installations) == 1
    assert installations[0]["installedBy"]["email"] == staff_user.email


def test_apps_installation_installed_by_without_manage_staff(
    app_installation, staff_api_client, permission_manage_apps, staff_user
):
    """MANAGE_STAFF is the only permission missing, so the denial is unambiguous."""
    # given
    app_installation.installed_by = staff_user
    app_installation.save(update_fields=["installed_by"])
    staff_api_client.user.user_permissions.add(permission_manage_apps)

    # when
    response = staff_api_client.post_graphql(APPS_INSTALLATION_QUERY_WITH_INSTALLED_BY)

    # then
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    error = content["errors"][0]
    assert error["extensions"]["exception"]["code"] == "PermissionDenied"
    assert error["message"] == MISSING_MANAGE_STAFF_MESSAGE


def test_apps_installation_installed_by_null(
    app_installation, staff_api_client, permission_manage_apps, permission_manage_staff
):
    # given - installation recorded before creator tracking existed
    assert app_installation.installed_by is None

    # when
    response = staff_api_client.post_graphql(
        APPS_INSTALLATION_QUERY_WITH_INSTALLED_BY,
        permissions=[permission_manage_apps, permission_manage_staff],
    )

    # then
    content = get_graphql_content(response)
    installations = content["data"]["appsInstallations"]
    assert len(installations) == 1
    assert installations[0]["installedBy"] is None


APPS_INSTALLATION_QUERY_WITH_LOGO = """
query ($size: Int, $format: IconThumbnailFormatEnum) {
  appsInstallations {
    id
    brand {
      logo {
        default(format: $format, size: $size)
      }
    }
  }
}
"""


@pytest.mark.parametrize(
    "format",
    [
        None,
        IconThumbnailFormat.WEBP,
        IconThumbnailFormat.ORIGINAL,
    ],
)
@pytest.mark.parametrize("thumbnail_exists", [True, False])
def test_apps_installations_query_logo_thumbnail_with_size_and_format_url_returned(
    thumbnail_exists,
    format,
    app_installation,
    staff_api_client,
    permission_manage_apps,
    icon_image,
    media_root,
):
    # given
    app_installation.brand_logo_default = icon_image
    app_installation.save()
    media_id = graphene.Node.to_global_id("AppInstallation", app_installation.uuid)
    if thumbnail_exists:
        thumbnail = Thumbnail.objects.create(
            app_installation=app_installation,
            size=128,
            format=format or IconThumbnailFormat.ORIGINAL,
            image=icon_image,
        )
        expected_url = f"https://example.com/media/{thumbnail.image.name}"
    else:
        expected_url = f"https://example.com/thumbnail/{media_id}/128/"
        if format not in [None, IconThumbnailFormat.ORIGINAL]:
            expected_url += f"{format}/"
    variables = {"size": 120, "format": format.upper() if format else None}
    # when
    response = staff_api_client.post_graphql(
        APPS_INSTALLATION_QUERY_WITH_LOGO,
        variables,
        permissions=[permission_manage_apps],
    )
    content = get_graphql_content(response)
    installations = content["data"]["appsInstallations"]
    # then
    assert len(installations) == 1
    thumbnail_url = installations[0]["brand"]["logo"]["default"]
    assert thumbnail_url == expected_url


@pytest.mark.parametrize(
    "format",
    [
        None,
        IconThumbnailFormat.WEBP,
        IconThumbnailFormat.ORIGINAL,
    ],
)
def test_apps_installations_query_logo_thumbnail_original_image_url_returned(
    format,
    app_installation,
    staff_api_client,
    permission_manage_apps,
    icon_image,
    media_root,
):
    # given
    app_installation.brand_logo_default = icon_image
    app_installation.save()
    expected_url = (
        f"https://example.com/media/{app_installation.brand_logo_default.name}"
    )
    variables = {"size": 0, "format": format.upper() if format else None}
    # when
    response = staff_api_client.post_graphql(
        APPS_INSTALLATION_QUERY_WITH_LOGO,
        variables,
        permissions=[permission_manage_apps],
    )
    content = get_graphql_content(response)
    installations = content["data"]["appsInstallations"]
    # then
    assert len(installations) == 1
    thumbnail_url = installations[0]["brand"]["logo"]["default"]
    assert thumbnail_url == expected_url
