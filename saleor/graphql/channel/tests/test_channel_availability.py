import graphene

from ....channel.error_codes import ChannelErrorCode
from ...tests.utils import get_graphql_content

CHANNEL_ACTIVATE_MUTATION = """
    mutation ActivateChannel($id: ID!) {
        channelActivate(id: $id){
            channel {
                id
                name
                isActive
            }
            channelErrors{
                field
                code
                message
            }
        }
    }
"""


def test_channel_activate_mutation(
    permission_manage_channels, staff_api_client, channel_USD
):
    # given
    channel_USD.is_active = False
    channel_USD.save()
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)

    variables = {"id": channel_id}
    # when
    response = staff_api_client.post_graphql(
        CHANNEL_ACTIVATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["channelActivate"]
    assert not data["channelErrors"]
    assert data["channel"]["name"] == channel_USD.name
    assert data["channel"]["isActive"] is True


def test_channel_activate_mutation_on_activated_channel(
    permission_manage_channels, staff_api_client, channel_USD
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)

    variables = {"id": channel_id}
    # when
    response = staff_api_client.post_graphql(
        CHANNEL_ACTIVATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["channelActivate"]
    assert data["channelErrors"][0]["field"] == "id"
    assert data["channelErrors"][0]["code"] == ChannelErrorCode.INVALID.name


CHANNEL_DEACTIVATE_MUTATION = """
    mutation DeactivateChannel($id: ID!) {
        channelDeactivate(id: $id){
            channel {
                id
                name
                isActive
            }
            channelErrors{
                field
                code
                message
            }
        }
    }
"""


def test_channel_deactivate_mutation(
    permission_manage_channels, staff_api_client, channel_USD
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)

    variables = {"id": channel_id}
    # when
    response = staff_api_client.post_graphql(
        CHANNEL_DEACTIVATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["channelDeactivate"]
    assert not data["channelErrors"]
    assert data["channel"]["name"] == channel_USD.name
    assert data["channel"]["isActive"] is False


def test_channel_deactivate_mutation_on_deactivated_channel(
    permission_manage_channels, staff_api_client, channel_USD
):
    # given
    channel_USD.is_active = False
    channel_USD.save()
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)

    variables = {"id": channel_id}
    # when
    response = staff_api_client.post_graphql(
        CHANNEL_DEACTIVATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["channelDeactivate"]
    assert data["channelErrors"][0]["field"] == "id"
    assert data["channelErrors"][0]["code"] == ChannelErrorCode.INVALID.name
