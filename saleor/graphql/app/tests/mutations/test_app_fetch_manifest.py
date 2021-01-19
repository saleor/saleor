from unittest.mock import Mock

import pytest
import requests

from ....tests.utils import assert_no_permission, get_graphql_content

APP_FETCH_MANIFEST_MUTATION = """
mutation AppFetchManifest($manifest_url: String!){
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
    }
    appErrors{
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
    errors = content["data"]["appFetchManifest"]["appErrors"]
    manifest = content["data"]["appFetchManifest"]["manifest"]
    assert not errors
    assert manifest["identifier"] == "app2"
    assert manifest["version"] == "1.0.0"
    assert manifest["about"] == "Lorem ipsum"
    assert manifest["name"] == "app"
    assert manifest["appUrl"] == "http://localhost:8888/app"
    assert manifest["configurationUrl"] == "htpp://localhost:8888/configuration"
    assert manifest["tokenTargetUrl"] == "http://localhost:3000/register"
    assert manifest["dataPrivacy"] == "Lorem ipsum"
    assert manifest["dataPrivacyUrl"] == "http://localhost:8888/app-data-privacy"
    assert manifest["homepageUrl"] == "http://localhost:8888/homepage"
    assert manifest["supportUrl"] == "http://localhost:8888/support"
    assert set([perm["code"] for perm in manifest["permissions"]]) == {
        "MANAGE_ORDERS",
        "MANAGE_USERS",
    }


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
    errors = content["data"]["appFetchManifest"]["appErrors"]
    manifest = content["data"]["appFetchManifest"]["manifest"]
    assert len(errors) == 1
    assert errors[0] == {
        "field": "permissions",
        "message": "Given permissions don't exist",
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
    errors = content["data"]["appFetchManifest"]["appErrors"]

    assert len(errors) == 1
    assert errors[0] == {
        "field": "manifestUrl",
        "message": "Unable to fetch manifest data.",
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
    errors = content["data"]["appFetchManifest"]["appErrors"]

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

    monkeypatch.setattr(requests, "get", mocked_get)
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
    errors = content["data"]["appFetchManifest"]["appErrors"]

    assert len(errors) == 1
    assert errors[0] == {
        "code": "INVALID",
        "field": "manifestUrl",
        "message": "Can't fetch manifest data. Please try later.",
    }
