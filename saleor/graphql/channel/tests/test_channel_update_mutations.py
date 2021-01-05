import graphene
from django.utils.text import slugify

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
    permission_manage_channels, staff_api_client, channel_USD
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
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
    channel_USD.refresh_from_db()
    assert channel_data["name"] == channel_USD.name == name
    assert channel_data["slug"] == channel_USD.slug == slug
    assert channel_data["currencyCode"] == channel_USD.currency_code == "USD"


def test_channel_update_mutation_as_app(
    permission_manage_channels, app_api_client, channel_USD
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
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
    channel_USD.refresh_from_db()
    assert channel_data["name"] == channel_USD.name == name
    assert channel_data["slug"] == channel_USD.slug == slug
    assert channel_data["currencyCode"] == channel_USD.currency_code == "USD"


def test_channel_update_mutation_as_customer(user_api_client, channel_USD):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    name = "newName"
    slug = "new_slug"
    variables = {"id": channel_id, "input": {"name": name, "slug": slug}}

    # when
    response = user_api_client.post_graphql(
        CHANNEL_UPDATE_MUTATION,
        variables=variables,
        permissions=(),
    )

    # then
    assert_no_permission(response)


def test_channel_update_mutation_as_anonymous(api_client, channel_USD):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    name = "newName"
    slug = "new_slug"
    variables = {"id": channel_id, "input": {"name": name, "slug": slug}}

    # when
    response = api_client.post_graphql(
        CHANNEL_UPDATE_MUTATION,
        variables=variables,
        permissions=(),
    )

    # then
    assert_no_permission(response)


def test_channel_update_mutation_slugify_slug_field(
    permission_manage_channels, staff_api_client, channel_USD
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
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
    channel_data = content["data"]["channelUpdate"]["channel"]
    assert channel_data["slug"] == slugify(slug)


def test_channel_update_mutation_with_duplicated_slug(
    permission_manage_channels, staff_api_client, channel_USD, channel_PLN
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
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
    permission_manage_channels, staff_api_client, channel_USD
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    name = "newName"
    slug = channel_USD.slug
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
    channel_USD.refresh_from_db()
    assert channel_data["name"] == channel_USD.name == name
    assert channel_data["slug"] == channel_USD.slug == slug
    assert channel_data["currencyCode"] == channel_USD.currency_code == "USD"


def test_channel_update_mutation_only_slug(
    permission_manage_channels, staff_api_client, channel_USD
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    name = channel_USD.name
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
    channel_USD.refresh_from_db()
    assert channel_data["name"] == channel_USD.name == name
    assert channel_data["slug"] == channel_USD.slug == slug
    assert channel_data["currencyCode"] == channel_USD.currency_code == "USD"
