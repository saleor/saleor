import graphene
import pytest
from freezegun import freeze_time

from .....app.models import App
from .....app.types import AppType
from .....core.jwt import create_access_token_for_app
from ....tests.utils import assert_no_permission, get_graphql_content

QUERY_APP = """
    query ($id: ID){
        app(id: $id){
            id
            created
            isActive
            permissions{
                code
            }
            tokens{
                authToken
            }
            webhooks{
                name
            }
            name
            type
            aboutApp
            dataPrivacy
            dataPrivacyUrl
            homepageUrl
            supportUrl
            configurationUrl
            appUrl
            accessToken
            extensions{
                id
                label
                url
                mount
                target
                permissions{
                    code
                }
            }
            metafield(key: "test")
            metafields(keys: ["test"])
            metadata{
                key
                value
            }
            privateMetadata{
                key
                value
            }
        }
    }
"""


@freeze_time("2012-01-14 11:00:00")
@pytest.mark.parametrize("app_type", ("external", "custom"))
def test_app_query(
    app_type,
    staff_api_client,
    permission_manage_apps,
    permission_manage_staff,
    app_with_token,
    external_app,
    webhook,
):
    app = app_with_token
    app = app if app_type == "custom" else external_app
    app.permissions.add(permission_manage_staff)
    app.store_value_in_metadata({"test": "123"})
    app.save()

    webhook = webhook
    webhook.app = app
    webhook.save()

    id = graphene.Node.to_global_id("App", app.id)
    variables = {"id": id}
    response = staff_api_client.post_graphql(
        QUERY_APP,
        variables,
        permissions=[permission_manage_apps],
    )
    content = get_graphql_content(response)

    tokens = app.tokens.all()
    app_data = content["data"]["app"]
    tokens_data = app_data["tokens"]
    assert tokens.count() == 1
    assert tokens_data[0]["authToken"] == tokens.first().auth_token[-4:]

    assert app_data["isActive"] == app.is_active
    assert app_data["permissions"] == [{"code": "MANAGE_STAFF"}]
    assert len(app_data["webhooks"]) == 1
    assert app_data["webhooks"][0]["name"] == webhook.name
    assert app_data["type"] == app.type.upper()
    assert app_data["aboutApp"] == app.about_app
    assert app_data["dataPrivacy"] == app.data_privacy
    assert app_data["dataPrivacyUrl"] == app.data_privacy_url
    assert app_data["homepageUrl"] == app.homepage_url
    assert app_data["supportUrl"] == app.support_url
    assert app_data["configurationUrl"] == app.configuration_url
    assert app_data["appUrl"] == app.app_url
    if app_type == "external":
        assert app_data["accessToken"] == create_access_token_for_app(
            app, staff_api_client.user
        )
    else:
        assert app_data["accessToken"] is None

    assert app_data["metadata"][0]["key"] == "test"
    assert app_data["metadata"][0]["value"] == "123"
    assert app_data["metafield"] == "123"
    assert app_data["metafields"] == {"test": "123"}


def test_app_query_no_permission(
    staff_api_client, permission_manage_staff, permission_manage_users, app
):
    app.permissions.add(permission_manage_staff)

    id = graphene.Node.to_global_id("App", app.id)
    variables = {"id": id}
    response = staff_api_client.post_graphql(QUERY_APP, variables, permissions=[])
    assert_no_permission(response)

    response = staff_api_client.post_graphql(
        QUERY_APP,
        variables,
        permissions=[permission_manage_users, permission_manage_staff],
    )
    assert_no_permission(response)


def test_app_with_access_to_resources(
    app_api_client,
    app,
    permission_manage_orders,
    order_with_lines,
):
    query = """
      query {
        orders(first: 5) {
          edges {
            node {
              id
            }
          }
        }
      }
    """
    response = app_api_client.post_graphql(query)
    assert_no_permission(response)
    response = app_api_client.post_graphql(
        query, permissions=[permission_manage_orders]
    )
    get_graphql_content(response)


def test_app_without_id_as_staff(
    staff_api_client, app, permission_manage_apps, order_with_lines, webhook
):
    # when
    response = staff_api_client.post_graphql(
        QUERY_APP, permissions=[permission_manage_apps], check_no_permissions=False
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["app"] is None


def test_own_app_without_id(
    app_api_client,
    app,
    order_with_lines,
    webhook,
):
    # given
    app.store_value_in_metadata({"public": "metadata"})
    app.store_value_in_private_metadata({"private": "metadata"})
    app.save()

    # when
    response = app_api_client.post_graphql(
        QUERY_APP,
    )

    # then
    content = get_graphql_content(response)

    tokens = app.tokens.all()
    app_data = content["data"]["app"]
    tokens_data = app_data["tokens"]
    assert tokens.count() == 1
    assert tokens_data[0]["authToken"] == tokens.first().auth_token[-4:]

    assert app_data["isActive"] == app.is_active
    assert len(app_data["webhooks"]) == 1
    assert app_data["webhooks"][0]["name"] == webhook.name
    assert app_data["type"] == app.type.upper()
    assert app_data["aboutApp"] == app.about_app
    assert app_data["dataPrivacy"] == app.data_privacy
    assert app_data["dataPrivacyUrl"] == app.data_privacy_url
    assert app_data["homepageUrl"] == app.homepage_url
    assert app_data["supportUrl"] == app.support_url
    assert app_data["configurationUrl"] == app.configuration_url
    assert app_data["appUrl"] == app.app_url
    assert app_data["metadata"][0]["key"] == "public"
    assert app_data["metadata"][0]["value"] == "metadata"
    assert app_data["privateMetadata"][0]["key"] == "private"
    assert app_data["privateMetadata"][0]["value"] == "metadata"


def test_app_query_without_permission(
    app_api_client,
    app,
    order_with_lines,
):
    # given
    second_app = App.objects.create(name="Sample app", is_active=True)
    id = graphene.Node.to_global_id("App", second_app.id)
    variables = {"id": id}

    # when
    response = app_api_client.post_graphql(
        QUERY_APP,
        variables,
    )

    # then
    assert_no_permission(response)


def test_app_query_without_permission_and_id(
    staff_api_client, app, order_with_lines, webhook
):
    # given
    App.objects.create(name="Sample app", is_active=True)

    # when
    response = staff_api_client.post_graphql(
        QUERY_APP,
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["app"]


def test_app_query_with_permission(
    app_api_client, permission_manage_apps, app, external_app, webhook
):
    app.permissions.add(permission_manage_apps)
    id = graphene.Node.to_global_id("App", app.id)
    variables = {"id": id}
    response = app_api_client.post_graphql(
        QUERY_APP,
        variables,
    )
    content = get_graphql_content(response)

    tokens = app.tokens.all()
    app_data = content["data"]["app"]
    tokens_data = app_data["tokens"]
    assert tokens.count() == 1
    assert tokens_data[0]["authToken"] == tokens.first().auth_token[-4:]

    assert app_data["isActive"] == app.is_active
    assert len(app_data["webhooks"]) == 1
    assert app_data["webhooks"][0]["name"] == webhook.name
    assert app_data["type"] == app.type.upper()
    assert app_data["aboutApp"] == app.about_app
    assert app_data["dataPrivacy"] == app.data_privacy
    assert app_data["dataPrivacyUrl"] == app.data_privacy_url
    assert app_data["homepageUrl"] == app.homepage_url
    assert app_data["supportUrl"] == app.support_url
    assert app_data["configurationUrl"] == app.configuration_url
    assert app_data["appUrl"] == app.app_url


def test_app_with_extensions_query(
    staff_api_client,
    permission_manage_apps,
    permission_manage_orders,
    app_with_extensions,
):
    app, app_extensions = app_with_extensions
    id = graphene.Node.to_global_id("App", app.id)
    variables = {"id": id}
    response = staff_api_client.post_graphql(
        QUERY_APP,
        variables=variables,
        permissions=[permission_manage_apps, permission_manage_orders],
    )
    content = get_graphql_content(response)
    app_data = content["data"]["app"]
    extensions_data = app_data["extensions"]
    returned_ids = {e["id"] for e in extensions_data}
    returned_labels = {e["label"] for e in extensions_data}
    returned_mounts = {e["mount"].lower() for e in extensions_data}
    returned_targets = {e["target"].lower() for e in extensions_data}
    returned_permission_codes = [e["permissions"] for e in extensions_data]
    for app_extension in app_extensions:
        global_id = graphene.Node.to_global_id("AppExtension", app_extension.id)
        assert global_id in returned_ids
        assert app_extension.label in returned_labels
        assert app_extension.mount in returned_mounts
        assert app_extension.target in returned_targets
        assigned_permissions = [p.codename for p in app_extension.permissions.all()]
        assigned_permissions = [{"code": p.upper()} for p in assigned_permissions]
        assert assigned_permissions in returned_permission_codes


QUERY_APP_AVAILABLE_FOR_STAFF_WITHOUT_MANAGE_APPS = """
    query ($id: ID){
        app(id: $id){
            id
            created
            isActive
            permissions{
                code
            }
            name
            type
            aboutApp
            dataPrivacy
            dataPrivacyUrl
            homepageUrl
            supportUrl
            configurationUrl
            appUrl
            accessToken
            extensions{
                id
                label
                url
                mount
                target
                permissions{
                    code
                }
            }
        }
    }
"""


@freeze_time("2012-01-14 11:00:00")
@pytest.mark.parametrize("app_type", ("external", "custom"))
def test_app_query_for_staff_without_manage_apps(
    app_type,
    staff_api_client,
    permission_manage_staff,
    app_with_token,
    external_app,
    webhook,
):
    app = app_with_token
    app = app if app_type == "custom" else external_app
    app.permissions.add(permission_manage_staff)

    webhook = webhook
    webhook.app = app
    webhook.save()

    id = graphene.Node.to_global_id("App", app.id)
    variables = {"id": id}
    response = staff_api_client.post_graphql(
        QUERY_APP_AVAILABLE_FOR_STAFF_WITHOUT_MANAGE_APPS,
        variables,
    )
    content = get_graphql_content(response)

    app_data = content["data"]["app"]

    assert app_data["isActive"] == app.is_active
    assert app_data["permissions"] == [{"code": "MANAGE_STAFF"}]
    assert app_data["type"] == app.type.upper()
    assert app_data["aboutApp"] == app.about_app
    assert app_data["dataPrivacy"] == app.data_privacy
    assert app_data["dataPrivacyUrl"] == app.data_privacy_url
    assert app_data["homepageUrl"] == app.homepage_url
    assert app_data["supportUrl"] == app.support_url
    assert app_data["configurationUrl"] == app.configuration_url
    assert app_data["appUrl"] == app.app_url
    if app_type == "external":
        assert app_data["accessToken"] == create_access_token_for_app(
            app, staff_api_client.user
        )
    else:
        assert app_data["accessToken"] is None


def test_app_query_for_normal_user(
    user_api_client, permission_manage_users, permission_manage_staff, app
):
    # when
    response = user_api_client.post_graphql(
        QUERY_APP_AVAILABLE_FOR_STAFF_WITHOUT_MANAGE_APPS,
    )

    # then
    assert_no_permission(response)


#
QUERY_APP_WITH_METADATA = """
    query ($id: ID){
        app(id: $id){
            id
            metadata{
                key
                value
            }
        }
    }
"""


def test_app_query_with_metadata_staff_user_without_permissions(
    staff_api_client,
    staff_user,
    app,
):
    # given
    app.type = AppType.THIRDPARTY
    app.store_value_in_metadata({"test": "123"})
    app.save()

    id = graphene.Node.to_global_id("App", app.id)
    variables = {"id": id}

    # when
    response = staff_api_client.post_graphql(QUERY_APP_WITH_METADATA, variables)

    # then
    assert_no_permission(response)


QUERY_APP_WITH_METAFIELD = """
    query ($id: ID){
        app(id: $id){
            id
            metafield(key: "test")
        }
    }
"""


def test_app_query_with_metafield_staff_user_without_permissions(
    staff_api_client,
    staff_user,
    app,
):
    # given
    app.type = AppType.THIRDPARTY
    app.store_value_in_metadata({"test": "123"})
    app.save()

    id = graphene.Node.to_global_id("App", app.id)
    variables = {"id": id}

    # when
    response = staff_api_client.post_graphql(QUERY_APP_WITH_METAFIELD, variables)

    # then
    assert_no_permission(response)


QUERY_APP_WITH_METAFIELDS = """
    query ($id: ID){
        app(id: $id){
            id
            metafields(keys: ["test"])
        }
    }
"""


def test_app_query_with_metafields_staff_user_without_permissions(
    staff_api_client,
    staff_user,
    app,
):
    # given
    app.type = AppType.THIRDPARTY
    app.store_value_in_metadata({"test": "123"})
    app.save()

    id = graphene.Node.to_global_id("App", app.id)
    variables = {"id": id}
    # when
    response = staff_api_client.post_graphql(
        QUERY_APP_WITH_METAFIELDS, variables=variables
    )

    # then
    assert_no_permission(response)
