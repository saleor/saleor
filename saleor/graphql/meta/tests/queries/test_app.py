import graphene

from ....tests.utils import assert_no_permission, get_graphql_content
from .utils import PRIVATE_KEY, PRIVATE_VALUE, PUBLIC_KEY, PUBLIC_VALUE

QUERY_APP_PRIVATE_META = """
    query appMeta($id: ID!){
        app(id: $id){
            privateMetadata{
                key
                value
            }
        }
    }
"""


def test_query_private_meta_for_app_as_anonymous_user(api_client, app):
    # given
    variables = {"id": graphene.Node.to_global_id("App", app.pk)}

    # when
    response = api_client.post_graphql(QUERY_APP_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_app_as_customer(user_api_client, app):
    # given
    variables = {"id": graphene.Node.to_global_id("App", app.pk)}

    # when
    response = user_api_client.post_graphql(QUERY_APP_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_app_as_staff(
    staff_api_client, app, permission_manage_apps
):
    # given
    app.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    app.save(update_fields=["private_metadata"])
    variables = {"id": graphene.Node.to_global_id("App", app.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_APP_PRIVATE_META,
        variables,
        [permission_manage_apps],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["app"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


def test_query_private_meta_for_app_as_app(app_api_client, app, permission_manage_apps):
    # given
    app.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    app.save(update_fields=["private_metadata"])
    variables = {"id": graphene.Node.to_global_id("App", app.pk)}

    # when
    response = app_api_client.post_graphql(
        QUERY_APP_PRIVATE_META,
        variables,
        [permission_manage_apps],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["app"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


QUERY_APP_PUBLIC_META = """
    query appMeta($id: ID!){
        app(id: $id){
            metadata{
                key
                value
            }
        }
    }
"""


def test_query_public_meta_for_app_as_anonymous_user(api_client, app):
    # given
    variables = {"id": graphene.Node.to_global_id("App", app.pk)}

    # when
    response = api_client.post_graphql(QUERY_APP_PUBLIC_META, variables)

    # then
    assert_no_permission(response)


def test_query_public_meta_for_app_as_customer(user_api_client, app):
    # given
    variables = {"id": graphene.Node.to_global_id("App", app.pk)}

    # when
    response = user_api_client.post_graphql(QUERY_APP_PUBLIC_META, variables)

    # then
    assert_no_permission(response)


def test_query_public_meta_for_app_as_staff(
    staff_api_client, app, permission_manage_apps
):
    # given
    app.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    app.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("App", app.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_APP_PUBLIC_META,
        variables,
        [permission_manage_apps],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["app"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_app_as_app(app_api_client, app, permission_manage_apps):
    # given
    app.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    app.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("App", app.pk)}

    # when
    response = app_api_client.post_graphql(
        QUERY_APP_PUBLIC_META,
        variables,
        [permission_manage_apps],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["app"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE
