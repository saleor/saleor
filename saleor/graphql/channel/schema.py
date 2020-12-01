import graphene

from ..decorators import staff_member_or_app_required
from .mutations import (
    ChannelActivate,
    ChannelCreate,
    ChannelDeactivate,
    ChannelDelete,
    ChannelUpdate,
)
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

    @staff_member_or_app_required
    def resolve_channel(self, info, id=None, **kwargs):
        return resolve_channel(info, id)

    @staff_member_or_app_required
    def resolve_channels(self, _info, **kwargs):
        return resolve_channels()


class ChannelMutations(graphene.ObjectType):
    channel_create = ChannelCreate.Field()
    channel_update = ChannelUpdate.Field()
    channel_delete = ChannelDelete.Field()
    channel_activate = ChannelActivate.Field()
    channel_deactivate = ChannelDeactivate.Field()
