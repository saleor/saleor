import graphene

from ....tests.utils import assert_no_permission, get_graphql_content
from .utils import PRIVATE_KEY, PRIVATE_VALUE, PUBLIC_KEY, PUBLIC_VALUE

QUERY_CHANNEL_PRIVATE_META = """
    query channelMeta($id: ID!){
        channel(id: $id){
            privateMetadata{
                key
                value
            }
        }
    }
"""


def test_query_private_meta_for_channel_as_anonymous_user(api_client, channel_USD):
    # given
    variables = {
        "id": graphene.Node.to_global_id("Channel", channel_USD.pk),
    }

    # when
    response = api_client.post_graphql(QUERY_CHANNEL_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_channel_as_customer(user_api_client, channel_USD):
    # given
    variables = {
        "id": graphene.Node.to_global_id("Channel", channel_USD.pk),
    }

    # when
    response = user_api_client.post_graphql(QUERY_CHANNEL_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_channel_as_staff(
    staff_api_client, channel_USD, permission_manage_channels
):
    # given
    channel_USD.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    channel_USD.save(update_fields=["private_metadata"])
    variables = {"id": graphene.Node.to_global_id("Channel", channel_USD.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_CHANNEL_PRIVATE_META,
        variables,
        [permission_manage_channels],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["channel"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


def test_query_private_meta_for_channel_as_app(
    app_api_client, channel_USD, permission_manage_channels
):
    # given
    channel_USD.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    channel_USD.save(update_fields=["private_metadata"])
    variables = {
        "id": graphene.Node.to_global_id("Channel", channel_USD.pk),
    }

    # when
    response = app_api_client.post_graphql(
        QUERY_CHANNEL_PRIVATE_META,
        variables,
        [permission_manage_channels],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["channel"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


QUERY_CHANNEL_PUBLIC_META = """
    query channelMeta($id: ID!){
        channel(id: $id){
            metadata{
                key
                value
            }
        }
    }
"""


def test_query_public_meta_for_channel_as_anonymous_user(api_client, channel_USD):
    # given
    channel_USD.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    channel_USD.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("Channel", channel_USD.pk)}

    # when
    response = api_client.post_graphql(QUERY_CHANNEL_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["channel"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_channel_as_customer(user_api_client, channel_USD):
    # given
    channel_USD.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    channel_USD.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("Channel", channel_USD.pk)}

    # when
    response = user_api_client.post_graphql(QUERY_CHANNEL_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["channel"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_channel_as_staff(
    staff_api_client, channel_USD, permission_manage_channels
):
    # given
    channel_USD.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    channel_USD.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("Channel", channel_USD.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_CHANNEL_PUBLIC_META,
        variables,
        [permission_manage_channels],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["channel"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_channel_as_app(
    app_api_client, channel_USD, permission_manage_channels
):
    # given
    channel_USD.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    channel_USD.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("Channel", channel_USD.pk)}

    # when
    response = app_api_client.post_graphql(
        QUERY_CHANNEL_PUBLIC_META,
        variables,
        [permission_manage_channels],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["channel"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE
