import graphene
import pytest

from .....thumbnail import IconThumbnailFormat
from .....thumbnail.models import Thumbnail
from ....tests.utils import assert_no_permission, get_graphql_content

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
    site_settings,
    icon_image,
    media_root,
):
    # given
    app_installation.brand_logo_default = icon_image
    app_installation.save()
    media_id = graphene.Node.to_global_id("AppInstallation", app_installation.uuid)
    domain = site_settings.site.domain
    if thumbnail_exists:
        thumbnail = Thumbnail.objects.create(
            app_installation=app_installation,
            size=128,
            format=format or IconThumbnailFormat.ORIGINAL,
            image=icon_image,
        )
        expected_url = f"http://{domain}/media/{thumbnail.image.name}"
    else:
        expected_url = f"http://{domain}/thumbnail/{media_id}/128/"
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
    site_settings,
    icon_image,
    media_root,
):
    # given
    app_installation.brand_logo_default = icon_image
    app_installation.save()
    domain = site_settings.site.domain
    expected_url = f"http://{domain}/media/{app_installation.brand_logo_default.name}"
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
