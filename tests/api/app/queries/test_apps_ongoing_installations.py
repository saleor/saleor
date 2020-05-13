from tests.api.utils import assert_no_permission, get_graphql_content

ONGOING_APPS_INSTALLATION_QUERY = """
    {
      appsOngoingInstallations{
        id
      }
    }
"""


def test_ongoing_apps_installation(app_job, staff_api_client, permission_manage_apps):

    response = staff_api_client.post_graphql(
        ONGOING_APPS_INSTALLATION_QUERY, permissions=[permission_manage_apps]
    )
    content = get_graphql_content(response)
    installations = content["data"]["appsOngoingInstallations"]
    assert len(installations) == 1
    assert int(installations[0]["id"]) == app_job.id


def test_ongoing_apps_installation_by_app(
    app_job, app_api_client, permission_manage_apps
):
    response = app_api_client.post_graphql(
        ONGOING_APPS_INSTALLATION_QUERY, permissions=[permission_manage_apps]
    )
    content = get_graphql_content(response)
    installations = content["data"]["appsOngoingInstallations"]
    assert len(installations) == 1
    assert int(installations[0]["id"]) == app_job.id


def test_ongoing_apps_installation_by_app_missing_permission(app_job, app_api_client):
    response = app_api_client.post_graphql(ONGOING_APPS_INSTALLATION_QUERY)
    assert_no_permission(response)


def test_ongoing_apps_installation_missing_permission(app_job, staff_api_client):
    response = staff_api_client.post_graphql(ONGOING_APPS_INSTALLATION_QUERY)
    assert_no_permission(response)
