import graphene

from ...core.permissions import ChannelPermission
from ..decorators import permission_required
from .mutations import ChannelCreate
from .resolvers import resolve_channel, resolve_channels
from .types import Channel


class ChannelQueries(graphene.ObjectType):
    channel = graphene.Field(
        Channel,
        id=graphene.Argument(graphene.ID, description="ID of the channel."),
        description="Look up a channel by ID.",
    )
    channels = graphene.List(
        graphene.NonNull(Channel), description="List of all channels."
    )

    @permission_required(ChannelPermission.MANAGE_CHANNELS)
    def resolve_channel(self, info, id=None, **kwargs):
        return resolve_channel(info, id)

    @permission_required(ChannelPermission.MANAGE_CHANNELS)
    def resolve_channels(self, _info, **kwargs):
        return resolve_channels()


class ChannelMutations(graphene.ObjectType):
    channel_create = ChannelCreate.Field()
