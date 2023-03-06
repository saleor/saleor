import graphene

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
