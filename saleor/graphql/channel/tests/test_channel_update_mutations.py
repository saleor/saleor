import graphene

from ....channel.error_codes import ChannelErrorCode
from ...tests.utils import assert_no_permission, get_graphql_content

CHANNEL_UPDATE_MUTATION = """
    mutation UpdateChannel($id: ID!,$input: ChannelUpdateInput!){
        channelUpdate(id: $id, input: $input){
            channel{
                id
                name
                slug
                currencyCode
            }
            channelErrors{
                field
                code
                message
            }
        }
    }
"""


def test_channel_update_mutation_as_staff_user(
    permission_manage_channels, staff_api_client, channel
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel.id)
    name = "newName"
    slug = "new_slug"
    variables = {"id": channel_id, "input": {"name": name, "slug": slug}}

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["channelUpdate"]
    assert not data["channelErrors"]
    channel_data = data["channel"]
    channel.refresh_from_db()
    assert channel_data["name"] == channel.name == name
    assert channel_data["slug"] == channel.slug == slug
    assert channel_data["currencyCode"] == channel.currency_code == "USD"


def test_channel_update_mutation_as_app(
    permission_manage_channels, app_api_client, channel
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel.id)
    name = "newName"
    slug = "new_slug"
    variables = {"id": channel_id, "input": {"name": name, "slug": slug}}

    # when
    response = app_api_client.post_graphql(
        CHANNEL_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["channelUpdate"]
    assert not data["channelErrors"]
    channel_data = data["channel"]
    channel.refresh_from_db()
    assert channel_data["name"] == channel.name == name
    assert channel_data["slug"] == channel.slug == slug
    assert channel_data["currencyCode"] == channel.currency_code == "USD"


def test_channel_update_mutation_as_customer(user_api_client, channel):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel.id)
    name = "newName"
    slug = "new_slug"
    variables = {"id": channel_id, "input": {"name": name, "slug": slug}}

    # when
    response = user_api_client.post_graphql(
        CHANNEL_UPDATE_MUTATION, variables=variables, permissions=(),
    )

    # then
    assert_no_permission(response)


def test_channel_update_mutation_as_anonymous(api_client, channel):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel.id)
    name = "newName"
    slug = "new_slug"
    variables = {"id": channel_id, "input": {"name": name, "slug": slug}}

    # when
    response = api_client.post_graphql(
        CHANNEL_UPDATE_MUTATION, variables=variables, permissions=(),
    )

    # then
    assert_no_permission(response)


def test_channel_update_mutation_with_invalid_slug(
    permission_manage_channels, staff_api_client, channel
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel.id)
    name = "testName"
    slug = "Invalid slug"
    variables = {"id": channel_id, "input": {"name": name, "slug": slug}}

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    error = content["data"]["channelUpdate"]["channelErrors"][0]
    assert error["field"] == "slug"
    assert error["code"] == ChannelErrorCode.INVALID.name


def test_channel_update_mutation_with_duplicated_slug(
    permission_manage_channels, staff_api_client, channel, channel_PLN
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel.id)
    name = "New Channel"
    slug = channel_PLN.slug
    variables = {"id": channel_id, "input": {"name": name, "slug": slug}}

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    error = content["data"]["channelUpdate"]["channelErrors"][0]
    assert error["field"] == "slug"
    assert error["code"] == ChannelErrorCode.UNIQUE.name


def test_channel_update_mutation_only_name(
    permission_manage_channels, staff_api_client, channel
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel.id)
    name = "newName"
    slug = channel.slug
    variables = {"id": channel_id, "input": {"name": name}}

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["channelUpdate"]
    assert not data["channelErrors"]
    channel_data = data["channel"]
    channel.refresh_from_db()
    assert channel_data["name"] == channel.name == name
    assert channel_data["slug"] == channel.slug == slug
    assert channel_data["currencyCode"] == channel.currency_code == "USD"


def test_channel_update_mutation_only_slug(
    permission_manage_channels, staff_api_client, channel
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel.id)
    name = channel.name
    slug = "new_slug"
    variables = {"id": channel_id, "input": {"slug": slug}}

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["channelUpdate"]
    assert not data["channelErrors"]
    channel_data = data["channel"]
    channel.refresh_from_db()
    assert channel_data["name"] == channel.name == name
    assert channel_data["slug"] == channel.slug == slug
    assert channel_data["currencyCode"] == channel.currency_code == "USD"
